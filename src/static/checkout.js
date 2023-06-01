let authHeader
async function getIdToken() {
  console.groupCollapsed("Requesting ID token...")

  const vaultV3 = document.getElementById('vault-v3').value
  const customerId = document.getElementById('customer-id').value
  let endpoint
  if (vaultV3 === 'MERCHANT') {
    endpoint = `/api/identity/id-token-with-auth/${customerId}`
  } else {
    endpoint = `/api/identity/id-token/${customerId}`
  }
  const idTokenResponse = await fetch(endpoint)
  const tokenData = await idTokenResponse.json()
  const { formatted, idToken, authHeader: myAuthHeader } = tokenData
  authHeader = myAuthHeader

  addApiCalls(formatted, click = false)

  console.log(`ID token: ${idToken}`)
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
  const tokenData = await clientTokenResponse.json()
  const { formatted, clientToken, authHeader: myAuthHeader } = tokenData
  authHeader = myAuthHeader

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
  query.set("vault", Boolean(options['vault-v3']))
  query.set('components', hosted ? 'hosted-fields' : 'buttons')
  query.set('enable-funding', 'card,venmo')
  // query.set('disable-funding', disableFunding)

  console.log(`PayPal JS SDK URL: ${url}`)

  const scriptElement = document.createElement('script')
  scriptElement.id = 'paypal-js-sdk'
  scriptElement.src = url.href

  if (document.getElementById('vault-v3').value !== '') {
    const idToken = await getIdToken()
    scriptElement.setAttribute('data-user-id-token', idToken)
  }

  if (hosted) {
    const clientToken = await getClientToken()
    scriptElement.setAttribute('data-client-token', clientToken)
  }

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
  const containerID = 'paypal-button-container'

  const newContainer = document.createElement('div')
  newContainer.setAttribute('id', containerID)

  const oldContainer = document.getElementById(containerID)
  oldContainer.replaceWith(newContainer)
}


function brandedClosure() {
  /*
   * This is a closure.
  **/
  let onClick = function ({ fundingSource }) {
    console.group("Button clicked!")
    console.log(`fundingSource: ${fundingSource}`)
    console.groupEnd()
  }
  let createOrder = async function ({ paymentSource }, actions) {
    console.group("Creating the order...")
    console.log(`paymentSource: ${paymentSource}`)

    console.log("Getting order options...")
    options = getOptions()
    options.authHeader = authHeader
    const createResp = await fetch("/api/orders/create", {
      headers: { "Content-Type": "application/json" },
      method: "POST",
      body: JSON.stringify(options),
    })
    const createData = await createResp.json()
    const { formatted, orderId: orderID } = createData
    authHeader = createData.authHeader

    addApiCalls(formatted)
    console.log(`Order ${orderID} created!`)

    console.groupEnd()
    return orderID
  }
  let onApprove = async function (data, actions) {
    console.group("Order approved!")
    const { paymentSource, orderID } = data
    console.log(`paymentSource: ${paymentSource}`)

    const captureResp = await fetch(`/api/orders/capture/${orderID}`, {
      headers: { "Content-Type": "application/json" },
      method: "POST",
      body: JSON.stringify(options),
    })
    const captureData = await captureResp.json()
    const { formatted, error } = captureData
    addApiCalls(formatted)
    console.groupEnd()

    if (error === "INSTRUMENT_DECLINED") {
      return actions.restart()
    }
  }
  let buttons
  async function loadButtons() {
    if (typeof buttons !== 'undefined') await buttons.close()
    buttons = await paypal.Buttons({
      onClick: onClick,
      createOrder: createOrder,
      onApprove: onApprove,
    })
    return buttons
      .render("#paypal-button-container")
      .catch((err) => {
        console.log(`Caught an error while rendering checkout: ${err}`)
      })
  }
  return loadButtons
}

function getContingencies() {
  return [document.getElementById('3ds-preference').value]
}

function hostedFieldsClosure() {
  /*
   * This is a closure.
  **/
  let orderID
  let createOrder = async function () {
    console.group("Creating the order...")
    console.log("Getting order options...")
    options = getOptions()
    options.authHeader = authHeader
    const createResp = await fetch('/api/orders/create', {
      headers: { 'Content-Type': 'application/json' },
      method: 'POST',
      body: JSON.stringify(options)
    })
    const createData = await createResp.json()
    const { formatted } = createData
    orderID = createData.orderId
    authHeader = createData.authHeader

    console.log(`Order ${orderID} created!`)
    addApiCalls(formatted)

    console.groupEnd()
    return orderID
  }
  let fields = {
    number: {
      selector: "#card-number",
      placeholder: "4111 1111 1111 1111"
    },
    cvv: {
      selector: "#cvv",
      placeholder: "123"
    },
    expirationDate: {
      selector: "#expiration-date",
      placeholder: "MM/YY"
    }
  }

  let hostedFields
  let onSubmit = async function (event) {
    event.preventDefault()
    await hostedFields.submit({
      // Cardholder's first and last name
      cardholderName: document.getElementById('card-holder-name').value,
      // Billing Address
      billingAddress: {
        streetAddress: document.getElementById('card-billing-address-street').value,
        extendedAddress: document.getElementById('card-billing-address-unit').value,
        region: document.getElementById('card-billing-address-state').value,
        locality: document.getElementById('card-billing-address-city').value,
        postalCode: document.getElementById('card-billing-address-zip').value,
        countryCodeAlpha2: document.getElementById('card-billing-address-country').value.toUpperCase()
      },
      // Trigger 3D Secure authentication
      contingencies: getContingencies()
    })

    console.group("Order approved!")
    console.log(`Getting status of order ${orderID}...`)
    const statusResp = await fetch(`/api/orders/status/${orderID}`, {
      headers: { 'Content-Type': 'application/json' },
      method: 'POST',
      body: JSON.stringify(options)
    })
    const status = await statusResp.json()
    addApiCalls(status.formatted)
    console.groupEnd()

    console.group('Capturing order...')
    const captureResp = await fetch(`/api/orders/capture/${orderID}`, {
      headers: { 'Content-Type': 'application/json' },
      method: 'POST',
      body: JSON.stringify(options)
    })
    console.log(`Captured order ${orderID}!`)
    const { details, formatted, debug_id: debugID } = await captureResp.json()
    addApiCalls(formatted)
    console.groupEnd()

    let errorDetail = Array.isArray(details) && details[0]
    if (errorDetail) {
      let msg = 'Sorry, your transaction could not be processed.'
      if (errorDetail.description) msg += `\n\n${errorDetail.description}`
      if (debugID) msg += ` (${debugID})`
      return alert(msg) // Show a failure message
    }
  }
  async function loadHostedFields() {
    if (paypal.HostedFields.isEligible()) {
      hostedFields = await paypal.HostedFields.render({
        createOrder: createOrder,
        fields: fields,
      })
      document.querySelector('#form-hosted-fields').onsubmit = onSubmit
    } else {
      alert("Not eligible for hosted fields. Sorry!")
      document.querySelector("#form-hosted-fields").style = 'display: none'
    }
  }
  return loadHostedFields
}

function addOnChange(loadCheckout) {
  console.groupCollapsed("Adding onChange...")
  const elementIds = [
    'intent',
    'customer-id',
    'vault-v3',
  ]
  for (const elementId of elementIds) {
    const element = document.getElementById(elementId)
    console.log(`Adding 'change' event listener to ${element}: ${loadCheckout}`)
    element.addEventListener('change', loadCheckout)
  }
  console.groupEnd()
}

