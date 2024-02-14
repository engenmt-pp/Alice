import {
  addApiCalls,
  getOptions,
  getPartnerMerchantInfo,
  saveOptions,
  setAuthHeader,
} from './utils.js'

function changeCheckout() {
  saveOptions()
  const newCheckoutURL = document.getElementById('checkout-method').value
  window.location.replace(newCheckoutURL)
}

/** Get a client token to be included in the JS SDK's script tag for (old) hosted fields. */
async function getClientToken() {
  console.groupCollapsed("Requesting client token...")

  const options = getOptions()
  const endpoint = "/api/identity/client-token"
  const clientTokenResponse = await fetch(endpoint, {
    headers: { "Content-Type": "application/json" },
    method: "POST",
    body: JSON.stringify(options),
  })
  const clientTokenData = await clientTokenResponse.json()
  const { formatted, clientToken, authHeader } = clientTokenData
  setAuthHeader(authHeader)

  addApiCalls(formatted, false)

  console.log(`Client token: ${clientToken}`)
  console.groupEnd()

  return clientToken
}

/** Get an ID token to be included in the JS SDK's script tag for vault purposes. */
async function getIdToken() {
  console.groupCollapsed("Requesting ID token...")

  const vaultLevel = document.getElementById('vault-level')?.value
  const customerId = document.getElementById('customer-id')?.value
  let endpoint = `/api/identity/id-token/${customerId}`
  if (vaultLevel === 'MERCHANT') {
    endpoint += `?include-auth-assertion=true`
  }

  const partnerMerchantInfo = getPartnerMerchantInfo()
  const idTokenResponse = await fetch(endpoint, {
    headers: { "Content-Type": "application/json" },
    method: "POST",
    body: JSON.stringify(partnerMerchantInfo),
  })
  const idTokenData = await idTokenResponse.json()
  const { formatted, idToken, authHeader } = idTokenData
  setAuthHeader(authHeader)

  addApiCalls(formatted, false)

  console.log('ID token:', idToken)
  console.groupEnd()

  return idToken
}

async function buildScriptElement(onload, checkoutMethod) {
  setAuthHeader('')
  const {
    intent,
    ...options
  } = getOptions()
  const url = new URL('https://www.paypal.com/sdk/js')

  const query = url.searchParams
  query.set("debug", false)
  query.set("client-id", options['partner-client-id'])
  query.set("merchant-id", options['merchant-id'])

  const currency = document.getElementById('currency-code')?.value || 'USD'
  query.set('currency', currency)

  const buyerCountry = document.getElementById('buyer-country-code')?.value
  if (buyerCountry) {
    query.set('buyer-country', buyerCountry)
  }

  const userAction = document.getElementById('user-action')?.value
  const commit = (userAction == 'CONTINUE')
  query.set('commit', commit)

  let components
  switch (checkoutMethod) {
    case 'branded':
      components = 'buttons'
      query.set('enable-funding', 'venmo,paylater,card')
      break
    case 'google-pay':
      components = 'googlepay'
      break
    case 'hosted-fields-v1':
      components = 'hosted-fields'
      break
    case 'hosted-fields-v2':
      components = 'card-fields'
      break
  }
  if (components) {
    query.set('components', components)
  }

  const vaultWithoutPurchase = document.querySelector('#vault-without-purchase:checked')
  if (vaultWithoutPurchase) {
    // When vaulting without purchase, the JS SDK will error out
    // if anything other than 'intent=capture' is passed.
    query.set("intent", "capture")
  } else if (intent) {
    query.set("intent", intent.toLowerCase())
  }

  const scriptElement = document.createElement('script')
  scriptElement.id = 'paypal-js-sdk'
  scriptElement.src = url.href
  console.log('PayPal JS SDK URL:', url.href)
  scriptElement.addEventListener('error', (event) => { console.log(event) })

  if (checkoutMethod == 'hosted-fields-v1') {
    const clientToken = await getClientToken()
    scriptElement.setAttribute('data-client-token', clientToken)
  }

  const vault = Boolean(options['vault-flow'])
  if (vault) {
    const idToken = await getIdToken()
    scriptElement.setAttribute('data-user-id-token', idToken)
  }

  const BNCode = options['partner-bn-code']
  scriptElement.setAttribute('data-partner-attribution-id', BNCode)

  scriptElement.addEventListener('load', onload)
  const oldScriptElement = document.getElementById('paypal-js-sdk')
  oldScriptElement.replaceWith(scriptElement)
}

function getContingencies() {
  const contingency = document.getElementById('3ds-preference')?.value
  if (contingency) {
    return [contingency]
  }
  return null
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
    'button-label',
    'merchant-id',
    'partner-client-id',
    'partner-secret',
    'partner-bn-code',
    'google-pay-button-color',
    'google-pay-button-type',
    'google-pay-button-locale',
  ]

  function innerAddOnChange(loadCheckout) {
    console.groupCollapsed("Updating 'change' event listeners...")
    if (myFunc != null) {
      console.log("Removing previous event listener:", myFunc)
      for (const elementId of elementIds) {
        const element = document.getElementById(elementId)
        if (element) {
          element.removeEventListener('change', myFunc)
        }
      }
    }
    myFunc = loadCheckout
    console.log("Adding new event listener:", myFunc)
    for (const elementId of elementIds) {
      const element = document.getElementById(elementId)
      if (element) {
        element.addEventListener('change', myFunc)
      }
    }
    console.groupEnd()
  }
  return innerAddOnChange
})()

function mapPaymentSource(paymentSource) {
  switch (paymentSource) {
    case "bancontact":
    case "credit":
    case "eps":
    case "giropay":
    case "ideal":
    case "mercadopago":
    case "mybank":
    case "paylater":
    case "p24":
    case "sofort":
    case "sepa":
      console.log(`Mapping paymentSource ${paymentSource} to 'paypal'!`)
      return 'paypal'
    case null:
    case undefined:
      console.log(`Mapping paymentSource ${paymentSource} to 'card'!`)
      return 'card'
    case "apple_pay":
    case "google_pay":
    case "paypal":
    case "venmo":
    default:
      console.log(`paymentSource ${paymentSource} was recevied!`)
      return paymentSource
  }
}

let orderId

function onClick({ fundingSource }) {
  console.group("Button clicked!")
  console.log('fundingSource:', fundingSource)
  console.groupEnd()
}

async function createOrder({ paymentSource } = {}) {
  console.group("Creating the order...")

  const options = getOptions()
  options['payment-source'] = mapPaymentSource(paymentSource)

  const createResp = await fetch("/api/orders/", {
    headers: { "Content-Type": "application/json" },
    method: "POST",
    body: JSON.stringify(options),
  })
  const createData = await createResp.json()
  const { formatted, authHeader } = createData;
  ({ orderId } = createData)
  setAuthHeader(authHeader)

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
  setAuthHeader(authHeader)

  addApiCalls(formatted)
}

async function captureOrder({ paymentSource, orderID, liabilityShift } = {}) {
  console.group(`Order approved!`)
  console.log('liabilityShift:', liabilityShift)

  if (orderID) {
    orderId = orderID
  } else {
    console.log(`No orderID received; defaulting to orderId = ${orderId}`)
  }
  console.log(`Capturing order ${orderId}...`)

  const options = getOptions()
  options['payment-source'] = mapPaymentSource(paymentSource)

  const captureResp = await fetch(`/api/orders/${orderId}/capture`, {
    headers: { 'Content-Type': 'application/json' },
    method: 'POST',
    body: JSON.stringify(options)
  })
  console.log(`Captured order ${orderId}!`)
  const captureData = await captureResp.json()
  const { formatted, authHeader, captureStatus } = captureData
  setAuthHeader(authHeader)

  addApiCalls(formatted)
  console.groupEnd()
  return captureStatus
}

async function createVaultSetupToken({ paymentSource } = {}) {
  console.group("Creating the vault setup token...")

  options = getOptions()
  options['payment-source'] = mapPaymentSource(paymentSource)

  const createResp = await fetch("/api/vault/setup-tokens", {
    headers: { "Content-Type": "application/json" },
    method: "POST",
    body: JSON.stringify(options),
  })
  const createData = await createResp.json()
  const { formatted, setupTokenId, authHeader } = createData
  setAuthHeader(authHeader)

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
  setAuthHeader(authHeader)

  addApiCalls(formatted)
  console.log(`Vault payment token ${paymentTokenId} created!`)
  console.groupEnd()
  return paymentTokenId
}

function onError(data) {
  console.group('Error!')
  console.log('data:', data)
  alert(`An error with the JS SDK occurred: ${data}\nCheck the console for more information.`)
  console.groupEnd()
}

export {
  addOnChange,
  buildScriptElement,
  changeCheckout,
  getIdToken,
  getContingencies,
  onClick,
  createOrder,
  getStatus,
  captureOrder,
  createVaultSetupToken,
  createVaultPaymentToken,
  onError,
}