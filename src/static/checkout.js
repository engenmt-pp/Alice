function changeCheckout() {
  saveOptions()
  const newCheckoutURL = document.getElementById('checkout-method').value
  window.location.replace(newCheckoutURL)
}

/** Get an ID token to be included in the JS SDK's script tag for vault purposes. */
async function getIdToken() {
  console.groupCollapsed("Requesting ID token...")

  const vaultLevel = document.getElementById('vault-level').value
  const customerId = document.getElementById('customer-id').value

  let endpoint = `/api/identity/id-token/${customerId}`
  if (vaultLevel === 'MERCHANT') {
    endpoint += `?include-auth-assertion=true`
  }
  const idTokenResponse = await fetch(endpoint)
  const idTokenData = await idTokenResponse.json()
  const { formatted, idToken, authHeader } = idTokenData
  document.getElementById('auth-header').value = authHeader

  addApiCalls(formatted, click = false)

  console.log('ID token:', idToken)
  console.groupEnd()

  return idToken
}

async function buildScriptElement(onload, checkoutMethod) {
  const {
    partnerClientId,
    merchantId,
    intent,
    ...options
  } = getOptions()
  const url = new URL('https://www.paypal.com/sdk/js')
  const query = url.searchParams
  query.set("client-id", partnerClientId)
  query.set("merchant-id", merchantId)
  const currencyElement = document.getElementById('currency-code')
  if (currencyElement != null) {
    query.set('currency', currencyElement.value)
  } else {
    console.log('No currency found! Defaulting to USD.')
    query.set('currency', 'USD')
  }

  const buyerCountryElement = document.getElementById('buyer-country-code')
  if (buyerCountryElement != null && buyerCountryElement.value != '') {
    query.set('buyer-country', buyerCountryElement.value)
  }
  query.set("debug", false)
  let commit
  if (document.getElementById('user-action').value == 'CONTINUE') {
    commit = false
  } else {
    commit = true
  }
  query.set('commit', commit)

  switch (checkoutMethod) {
    case 'branded':
      query.set('components', 'buttons')
      query.set('enable-funding', 'venmo,paylater,card')
      break
    case 'hosted-fields-v1':
      query.set('components', 'hosted-fields')
      break
    case 'hosted-fields-v2':
      query.set('components', 'card-fields')
      break
  }

  if (document.getElementById('vault-without-purchase').checked) {
    // When vaulting without purchase, the JS SDK will error out
    // if anything other than 'intent=capture' is passed.
    query.set("intent", "capture")
  } else {
    query.set("intent", intent.toLowerCase())
  }

  const scriptElement = document.createElement('script')
  scriptElement.id = 'paypal-js-sdk'
  scriptElement.src = url.href
  console.log('PayPal JS SDK URL:', url.href)

  if (checkoutMethod == 'hosted-fields-v1') {
    const clientToken = await getClientToken()
    scriptElement.setAttribute('data-client-token', clientToken)
  }

  const vault = Boolean(options['vault-flow'])
  if (vault) {
    const idToken = await getIdToken()
    scriptElement.setAttribute('data-user-id-token', idToken)
  }
  scriptElement.setAttribute('onerror', (event) => { console.log(event) })

  const BNCode = options['partner-bn-code']
  scriptElement.setAttribute('data-partner-attribution-id', BNCode)

  scriptElement.onload = onload
  const oldScriptElement = document.getElementById('paypal-js-sdk')
  oldScriptElement.replaceWith(scriptElement)
}


function getContingencies() {
  return [document.getElementById('3ds-preference').value]
}

function buyerNotPresentCheckout() {
  let options
  async function createOrder({ paymentSource }) {
    console.group("Creating the order...")
    console.log('paymentSource:', paymentSource)

    console.log("Getting order options...")
    options = getOptions()
    options['vault-flow'] = "buyer-not-present"
    options['payment-source'] = paymentSource
    const createResp = await fetch("/api/orders/", {
      headers: { "Content-Type": "application/json" },
      method: "POST",
      body: JSON.stringify(options),
    })
    const createData = await createResp.json()
    const { formatted, orderId, authHeader } = createData
    document.getElementById('auth-header').value = authHeader

    addApiCalls(formatted)

    if (orderId == null) {
      console.log('Order creation failed!')
      alert('Order creation failed!')
      // throw new Error('Order creation failed!')
    } else {
      console.log(`Order ${orderId} created!`)
    }
    console.groupEnd()
    return orderId
  }
  async function authorizeAndOrCaptureOrder({ paymentSource, orderId }) {
    console.group(`Authorizing and/or capturing order ${orderId}!`)
    console.log('paymentSource:', paymentSource)

    options.authHeader = authHeader
    const captureResp = await fetch(`/api/orders/${orderId}/capture`, {
      headers: { "Content-Type": "application/json" },
      method: "POST",
      body: JSON.stringify(options),
    })
    const captureData = await captureResp.json()
    const { formatted, error, authHeader } = captureData
    document.getElementById('auth-header').value = authHeader

    addApiCalls(formatted)
    console.groupEnd()

    if (error === "INSTRUMENT_DECLINED") {
      return actions.restart()
    }
  }
  async function payWithVaultedPaymentToken() {
    console.group("Initiating buyer-not-present checkout...")

    const paymentTokenId = document.getElementById('vault-id').value
    if (paymentTokenId == null || paymentTokenId == '') {
      return alert("A payment token must be provided for buyer-not-present orders!")
    }

    const paymentSource = document.getElementById('vault-payment-source').value
    console.log('paymentSource:', paymentSource)

    const myOptions = { paymentSource: paymentSource }

    const orderId = await createOrder(myOptions)
    myOptions.orderId = orderId

    if (options.intent === 'AUTHORIZE') {
      await authorizeAndOrCaptureOrder(myOptions)
    } else {
      console.log('Order should be complete!')
    }

    console.groupEnd()
  }
  return payWithVaultedPaymentToken
}

let addOnChange = (function () {
  let myFunc
  const elementIds = [
    'intent',
    'vault-flow',
    'vault-level',
    'vault-without-purchase',
    'user-action',
    'customer-id',
    'currency-code',
    'buyer-country-code',
    'button-label'
  ]

  function innerAddOnChange(loadCheckout) {
    console.groupCollapsed("Updating 'change' event listeners...")
    if (myFunc != null) {
      console.log("Removing previous event listener:", myFunc)
      for (const elementId of elementIds) {
        const element = document.getElementById(elementId)
        if (element != null) {
          element.removeEventListener('change', myFunc)
        }
      }
    }
    myFunc = loadCheckout
    console.log("Adding new event listener:", myFunc)
    for (const elementId of elementIds) {
      const element = document.getElementById(elementId)
      if (element != null) {
        element.addEventListener('change', myFunc)
      }
    }
    console.groupEnd()
  }
  return innerAddOnChange
})()

function checkoutFunctions() {
  let orderId
  function onClick({ fundingSource }) {
    console.group("Button clicked!")
    console.log('fundingSource:', fundingSource)
    console.groupEnd()
  }
  async function createOrder({ paymentSource } = {}) {
    console.group("Creating the order...")
    console.log('paymentSource:', paymentSource)

    const options = getOptions()
    if (paymentSource != null) {
      options['payment-source'] = paymentSource
    }
    const createResp = await fetch("/api/orders/", {
      headers: { "Content-Type": "application/json" },
      method: "POST",
      body: JSON.stringify(options),
    })
    const createData = await createResp.json()
    const { formatted, authHeader } = createData;
    ({ orderId } = createData)
    document.getElementById('auth-header').value = authHeader

    addApiCalls(formatted)
    console.log(`Order ${orderId} created!`)
    console.groupEnd()
    return orderId
  }
  async function getStatus() {
    console.log(`Getting status of order ${orderId}...`)

    const options = getOptions()
    const statusResp = await fetch(`/api/orders/${orderId}`, {
      headers: { 'Content-Type': 'application/json' },
      method: 'POST',
      body: JSON.stringify(options)
    })
    const statusData = await statusResp.json()
    const { formatted, authHeader } = statusData
    document.getElementById('auth-header').value = authHeader

    addApiCalls(formatted)
  }
  async function captureOrder({ paymentSource, orderID } = {}) {
    if (orderID != null) {
      orderId = orderID
    }
    console.group(`Order ${orderId} was approved!`)
    console.log('paymentSource:', paymentSource)
    console.log(`Capturing order ${orderId}...`)

    const options = getOptions()
    const captureResp = await fetch(`/api/orders/${orderId}/capture`, {
      headers: { 'Content-Type': 'application/json' },
      method: 'POST',
      body: JSON.stringify(options)
    })
    console.log(`Captured order ${orderId}!`)
    const captureData = await captureResp.json()
    const { formatted, authHeader } = captureData
    document.getElementById('auth-header').value = authHeader

    addApiCalls(formatted)
    console.groupEnd()
  }
  async function createVaultSetupToken({ paymentSource } = {}) {
    console.group("Creating the vault setup token...")
    console.log('paymentSource:', paymentSource)

    options = getOptions()
    if (paymentSource != null) {
      options['payment-source'] = paymentSource
    }
    const createResp = await fetch("/api/vault/setup-tokens", {
      headers: { "Content-Type": "application/json" },
      method: "POST",
      body: JSON.stringify(options),
    })
    const createData = await createResp.json()
    const { formatted, setupTokenId, authHeader } = createData
    document.getElementById('auth-header').value = authHeader

    addApiCalls(formatted)
    console.log(`Vault setup token ${setupTokenId} created!`)
    console.groupEnd()
    return setupTokenId
  }
  async function createVaultPaymentToken({ vaultSetupToken: setupTokenId } = {}) {
    console.log(`Vault setup token ${setupTokenId} was approved!`)
    console.group('Creating vault payment token...')

    const createResp = await fetch(`/api/vault/setup-tokens/${setupTokenId}`, {
      headers: { "Content-Type": "application/json" },
      method: "POST",
      body: JSON.stringify(options),
    })
    const createData = await createResp.json()
    const { formatted, paymentTokenId, authHeader } = createData
    document.getElementById('auth-header').value = authHeader

    addApiCalls(formatted)
    console.log(`Vault payment token ${paymentTokenId} created!`)
    console.groupEnd()
    return paymentTokenId
  }
  function onError(data) {
    console.group('Error!')
    console.log('data:', data)
    alert("An error with the JS SDK occurred! Check the console for more information.")
    console.groupEnd()
  }
  return {
    onClick: onClick,
    createOrder: createOrder,
    getStatus: getStatus,
    captureOrder: captureOrder,
    createVaultSetupToken: createVaultSetupToken,
    createVaultPaymentToken: createVaultPaymentToken,
    onError: onError,
  }
}