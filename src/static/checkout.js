let authHeader
async function getIdToken() {
  console.groupCollapsed("Requesting ID token...")

  const vaultLevel = document.getElementById('vault-level').value
  const customerId = document.getElementById('customer-id').value
  console.log("vaultLevel:", vaultLevel)
  console.log("customerId:", customerId)
  let endpoint = `/api/identity/id-token/${customerId}`
  if (vaultLevel === 'MERCHANT') {
    endpoint += `?include-auth-assertion=true`
  }
  console.log('endpoint:', endpoint)
  const idTokenResponse = await fetch(endpoint)
  const idTokenData = await idTokenResponse.json()
  const { formatted, idToken } = idTokenData;
  ({ authHeader } = idTokenData)

  addApiCalls(formatted, click = false)

  console.log('ID token:', idToken)
  console.groupEnd()

  return idToken
}

async function getClientToken() {
  console.groupCollapsed("Requesting Client token...")

  const endpoint = "/api/identity/client-token"
  const clientTokenResponse = await fetch(endpoint, {
    headers: { "Content-Type": "application/json" },
    method: "POST",
    body: JSON.stringify({ authHeader: authHeader }),
  })
  const clientTokenData = await clientTokenResponse.json()
  const { formatted, clientToken } = clientTokenData;
  ({ authHeader } = clientTokenData)

  addApiCalls(formatted, click = false)

  console.log(`Client token: ${clientToken}`)
  console.groupEnd()

  return clientToken
}

async function buildScriptElement(onload, hosted = false) {
  const {
    partnerClientId,
    merchantId,
    intent,
    currency,
    ...options
  } = getOptions()
  const url = new URL('https://www.paypal.com/sdk/js')
  const query = url.searchParams
  query.set("client-id", partnerClientId)
  query.set("merchant-id", merchantId)
  query.set("intent", intent.toLowerCase())
  query.set("currency", currency)
  query.set("commit", true)
  query.set('components', hosted ? 'hosted-fields' : 'buttons,card-fields')
  query.set('enable-funding', 'card,paylater,venmo')
  const vault = Boolean(options['vault-level'])
  query.set("vault", vault)

  console.log(`PayPal JS SDK URL: ${url}`)

  const scriptElement = document.createElement('script')
  scriptElement.id = 'paypal-js-sdk'
  scriptElement.src = url.href

  if (hosted) {
    const clientToken = await getClientToken()
    scriptElement.setAttribute('data-client-token', clientToken)
  }
  if (vault) {
    const idToken = await getIdToken()
    scriptElement.setAttribute('data-user-id-token', idToken)
  }

  scriptElement.setAttribute('onerror', (event) => { console.log(event) })

  const BNCode = options['bn-code']
  scriptElement.setAttribute('data-partner-attribution-id', BNCode)

  scriptElement.onload = onload
  const oldScriptElement = document.getElementById('paypal-js-sdk')
  oldScriptElement.replaceWith(scriptElement)
}

async function resetButtonContainer() {
  /*
   * Replace the button container with an empty div.
  **/
  const containerId = 'paypal-button-container'

  const newContainer = document.createElement('div')
  newContainer.setAttribute('id', containerId)

  const oldContainer = document.getElementById(containerId)
  oldContainer.replaceWith(newContainer)
}

function brandedClosure() {
  let options
  let onClick = function ({ fundingSource }) {
    console.group("Button clicked!")
    console.log('fundingSource:', fundingSource)
    console.groupEnd()
  }
  let createVaultSetupToken = async function ({ paymentSource }) {
    console.group("Creating the vault setup token...")
    console.log('paymentSource:', paymentSource)

    console.log("Getting order options...")
    options = getOptions()
    const createResp = await fetch("/api/vault/setup-tokens", {
      headers: { "Content-Type": "application/json" },
      method: "POST",
      body: JSON.stringify(options),
    })
    const createData = await createResp.json()
    const { formatted, setupTokenId } = createData;
    ({ authHeader } = createData)

    addApiCalls(formatted)
    console.log(`Vault setup token ${setupTokenId} created!`)
    console.groupEnd()
    return setupTokenId
  }
  let createOrder = async function ({ paymentSource }) {
    console.group("Creating the order...")
    console.log('paymentSource:', paymentSource)

    console.log("Getting order options...")
    options = getOptions()
    const createResp = await fetch("/api/orders/create", {
      headers: { "Content-Type": "application/json" },
      method: "POST",
      body: JSON.stringify(options),
    })
    const createData = await createResp.json()
    const { formatted, orderId } = createData;
    ({ authHeader } = createData)

    addApiCalls(formatted)
    console.log(`Order ${orderId} created!`)
    console.groupEnd()
    return orderId
  }
  let onApprove = async function ({ paymentSource, orderID: orderId }, actions) {
    console.group(`Order ${orderId} was approved!`)
    console.log('paymentSource:', paymentSource)

    const captureResp = await fetch(`/api/orders/capture/${orderId}`, {
      headers: { "Content-Type": "application/json" },
      method: "POST",
      body: JSON.stringify(options),
    })
    const captureData = await captureResp.json()
    const { formatted, error } = captureData;
    ({ authHeader } = captureData)
    addApiCalls(formatted)
    console.groupEnd()

    if (error === "INSTRUMENT_DECLINED") {
      return actions.restart()
    }
  }
  let createVaultPaymentToken = async function ({ vaultSetupToken }) {
    console.group(`Vault setup token ${vaultSetupToken} was approved!`)
    console.log('Creating vault token...')
    options['setup-token'] = vaultSetupToken
    const createResp = await fetch(`/api/vault/setup-tokens/${vaultSetupToken}`, {
      headers: { "Content-Type": "application/json" },
      method: "POST",
      body: JSON.stringify(options),
    })
    const createData = await createResp.json()
    const { formatted, paymentTokenId } = createData;
    ({ authHeader } = createData)

    addApiCalls(formatted)
    console.log(`Vault payment token ${paymentTokenId} created!`)
    console.groupEnd()
    return paymentTokenId
  }
  let buttons
  async function loadButtons() {
    if (typeof buttons !== 'undefined') await buttons.close()
    let methods
    const vaultPref = document.getElementById('vault-preference').value
    if (vaultPref === 'without-purchase') {
      methods = {
        onClick: onClick,
        createVaultSetupToken: createVaultSetupToken,
        onApprove: createVaultPaymentToken,
      }
    } else {
      methods = {
        onClick: onClick,
        createOrder: createOrder,
        onApprove: onApprove,
      }
    }
    buttons = await paypal.Buttons(methods)
    return buttons
      .render("#paypal-button-container")
      .catch((err) => {
        console.log('Caught an error while rendering checkout:', err)
      })
  }
  loadButtons.buttons = buttons
  return loadButtons
}

function cardFieldsClosure() {
  let options
  let createOrder = async function ({ paymentSource } = {}) {
    console.group("Creating the order...")
    console.log('paymentSource:', paymentSource)

    console.log("Getting order options...")
    options = getOptions()
    const createResp = await fetch('/api/orders/create', {
      headers: { 'Content-Type': 'application/json' },
      method: 'POST',
      body: JSON.stringify(options)
    })
    const createData = await createResp.json()
    const { formatted, orderId } = createData;
    ({ authHeader } = createData)
    addApiCalls(formatted)

    console.log(`Order ${orderId} created!`)
    console.groupEnd()
    return orderId
  }
  let onApprove = async function ({ paymentSource, orderID: orderId }) {
    console.group(`Order ${orderId} was approved!`)
    console.log('paymentSource:', paymentSource)

    console.log(`Getting status of order ${orderId}...`)
    const statusResp = await fetch(`/api/orders/status/${orderId}`, {
      headers: { 'Content-Type': 'application/json' },
      method: 'POST',
      body: JSON.stringify(options)
    })
    const statusData = await statusResp.json()
    const { formatted: statusFormatted } = statusData
    addApiCalls(statusFormatted)
    console.groupEnd()

    console.group(`Capturing order ${orderId}...`)
    const captureResp = await fetch(`/api/orders/capture/${orderId}`, {
      headers: { 'Content-Type': 'application/json' },
      method: 'POST',
      body: JSON.stringify(options)
    })
    const captureData = await captureResp.json()
    const { formatted: captureFormatted } = captureData

    addApiCalls(captureFormatted)
    console.groupEnd()
  }
  let cardFields
  async function loadCardFields() {
    if (typeof cardFields !== 'undefined') await buttons.close()
    let methods = {
      createOrder: createOrder,
      onApprove: onApprove,
    }
    cardFields = paypal.CardFields({
      styles: {
        '.valid': { 'color': 'green' },
        '.invalid': { 'color': 'red' }
      },
      ...methods
    })
    if (cardFields.isEligible()) {
      const nameField = cardFields.NameField()
      await nameField.render('#cf-card-holder-name')

      const numberField = cardFields.NumberField()
      await numberField.render('#cf-card-number')

      const cvvField = cardFields.CVVField()
      await cvvField.render('#cf-cvv')

      const expiryField = cardFields.ExpiryField()
      await expiryField.render('#cf-expiration-date')

      document.querySelector("#form-cf-card").addEventListener('submit', (event) => {
        event.preventDefault()
        cardFields.submit()
      })
    } else {
      alert("Not eligible for CardFields!")
    }
  }
  loadCardFields.cardFields = cardFields
  return loadCardFields
}

function getContingencies() {
  return [document.getElementById('3ds-preference').value]
}

function hostedFieldsClosure() {
  let orderId
  let options
  let createOrder = async function () {
    console.group("Creating the order...")

    console.log("Getting order options...")
    options = getOptions();
    ({ authHeader } = options)
    const createResp = await fetch('/api/orders/create', {
      headers: { 'Content-Type': 'application/json' },
      method: 'POST',
      body: JSON.stringify(options)
    })
    const createData = await createResp.json()
    const { formatted } = createData;
    ({ orderId, authHeader } = createData)

    console.log(`Created order ${orderId}!`)
    addApiCalls(formatted)

    console.groupEnd()
    return orderId
  }
  let fields = {
    number: {
      selector: "#hf-card-number",
      placeholder: "4111 1111 1111 1111"
    },
    cvv: {
      selector: "#hf-cvv",
      placeholder: "123"
    },
    expirationDate: {
      selector: "#hf-expiration-date",
      placeholder: "MM/YY"
    }
  }

  async function getStatus() {
    console.log(`Getting status of order ${orderId}...`)
    const statusResp = await fetch(`/api/orders/status/${orderId}`, {
      headers: { 'Content-Type': 'application/json' },
      method: 'POST',
      body: JSON.stringify(options)
    })
    const statusData = await statusResp.json()
    const { formatted } = statusData
    addApiCalls(formatted)
    console.groupEnd()
  }
  async function captureOrder() {
    console.group(`Capturing order ${orderId}...`)
    const captureResp = await fetch(`/api/orders/capture/${orderId}`, {
      headers: { 'Content-Type': 'application/json' },
      method: 'POST',
      body: JSON.stringify(options)
    })
    console.log(`Captured order ${orderId}!`)
    const captureData = await captureResp.json()
    const { details, formatted, debug_id: debugId } = captureData
    addApiCalls(formatted)
    console.groupEnd()

    let errorDetail = Array.isArray(details) && details[0]
    if (errorDetail) {
      let msg = 'Sorry, your transaction could not be processed.'
      if (errorDetail.description) msg += `\n\n${errorDetail.description}`
      if (debugId) msg += ` (${debugId})`
      return alert(msg) // Show a failure message
    }
  }

  let hostedFields
  let onSubmit = async function (event) {
    event.preventDefault()
    await hostedFields.submit({
      // Cardholder's first and last name
      cardholderName: document.getElementById('hf-card-holder-name').value,
      // Billing Address
      billingAddress: {
        streetAddress: document.getElementById('hf-billing-address-street').value,
        extendedAddress: document.getElementById('hf-billing-address-unit').value,
        region: document.getElementById('hf-billing-address-state').value,
        locality: document.getElementById('hf-billing-address-city').value,
        postalCode: document.getElementById('hf-billing-address-zip').value,
        countryCodeAlpha2: document.getElementById('hf-billing-address-country').value.toUpperCase()
      },
      // Trigger 3D Secure authentication
      contingencies: getContingencies()
    })

    console.group("Order approved!")
    await getStatus()
    await captureOrder()
  }
  async function loadHostedFields() {
    if (paypal.HostedFields.isEligible()) {
      hostedFields = await paypal.HostedFields.render({
        createOrder: createOrder,
        fields: fields,
      })
      document.getElementById('form-hf-card').onsubmit = onSubmit
    } else {
      alert("Not eligible for hosted fields. Sorry!")
      document.getElementById("form-hf-card").style = 'display: none'
    }
  }
  return loadHostedFields
}

function addOnChange(loadCheckout) {
  console.groupCollapsed("Adding onChange...")
  const elementIds = [
    'intent',
    'customer-id',
    'vault-level',
    'vault-preference',
  ]
  for (const elementId of elementIds) {
    const element = document.getElementById(elementId)
    console.log(`Adding 'change' event listener to ${element}: ${loadCheckout}`)
    element.addEventListener('change', loadCheckout)
  }
  console.groupEnd()
}

