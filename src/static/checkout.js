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


async function buildScriptElement(onload) {
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

  console.log(`url: ${url}`)

  // query.set('components', components)
  // query.set('enable-funding', enableFunding)
  // query.set('disable-funding', disableFunding)

  const scriptElement = document.createElement('script')
  scriptElement.id = 'paypal-js-sdk'
  scriptElement.src = url.href

  const idToken = await getIdToken()
  scriptElement.setAttribute('data-user-id-token', idToken)

  // scriptElement.setAttribute('data-client-token', dataClientToken)

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

    options = getOptions()
    const res = await fetch("/api/orders/create", {
      headers: { "Content-Type": "application/json" },
      method: "POST",
      body: JSON.stringify(options),
    })
    const createData = await res.json()
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

    const res = await fetch(`/api/orders/capture/${orderID}`, {
      headers: { "Content-Type": "application/json" },
      method: "POST",
      body: JSON.stringify(options),
    })
    const captureData = await res.json()
    const { formatted, error } = captureData
    addApiCalls(formatted)
    console.groupEnd()

    if (error === "INSTRUMENT_DECLINED") {
      return actions.restart()
    }
  }
  let buttons
  async function loadButtons() {
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

  async function reloadButtons() {
    await buttons.close()
    await buildScriptElement(() => {
      resetButtonContainer()
      loadButtons()
    })
  }
  buildScriptElement(loadButtons)
  return reloadButtons
}

function addOnChange(reloadButtons) {
  const elementIDs = [
    'intent',
    'customer-id',
    'vault-v3',
  ]
  for (const elementID of elementIDs) {
    const element = document.getElementById(elementID)
    element.addEventListener('change', (event) => {
      reloadButtons()
    })
  }
}