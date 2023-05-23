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
  const responseJson = await idTokenResponse.json()
  console.log("Response JSON:", JSON.stringify(responseJson, null, 2))

  const formatted = responseJson['formatted']
  addApiCalls(formatted, click = false)

  let idToken
  if (responseJson.hasOwnProperty('id-token')) {
    idToken = responseJson['id-token']
    console.log(`ID token: ${idToken}`)
  }
  if (responseJson.hasOwnProperty('auth-header')) {
    authHeader = responseJson['auth-header']
  }

  console.groupEnd()
  return idToken
}


async function buildScriptElement(onload) {
  const options = getOptions()
  const url = new URL('https://www.paypal.com/sdk/js')
  url.searchParams.append("client-id", options['partner-client-id'])
  url.searchParams.append("merchant-id", options['merchant-id'])
  url.searchParams.append("intent", options['intent'].toLowerCase())
  url.searchParams.append("currency", options['currency'])
  url.searchParams.append("commit", true)

  url.searchParams.append("vault", Boolean(options['vault-v3']))

  console.log('url:', url)

  // url.searchParams.append('components', components)
  // url.searchParams.append('enable-funding', enableFunding)
  // url.searchParams.append('disable-funding', disableFunding)

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
  let orderId
  let onClick = function (data) {
    console.group("Button clicked!")
    const fundingSource = data.fundingSource
    console.log("fundingSource:", fundingSource)
    console.groupEnd()
  }
  let createOrder = async function (data, actions) {
    console.group("Creating the order...")

    const paymentSource = data.paymentSource
    console.log(`paymentSource: ${paymentSource}`)

    options = getOptions()
    const res = await fetch("/api/orders/create", {
      headers: { "Content-Type": "application/json" },
      method: "POST",
      body: JSON.stringify(options),
    })
    const createData = await res.json()

    addApiCalls(createData.formatted)

    authHeader = createData.authHeader

    orderId = createData.orderId
    console.log(`Order ${orderId} created!`
    )
    console.groupEnd()
    return orderId
  }
  let onApprove = async function (data, actions) {
    console.group("Order approved!")
    const paymentSource = data.paymentSource
    console.log(`paymentSource: ${paymentSource}`)
    // TODO: Replace with const { paymentSource, orderID } = data

    const res = await fetch(`/api/orders/capture/${data.orderID}`, {
      headers: { "Content-Type": "application/json" },
      method: "POST",
      body: JSON.stringify(options),
    })
    const captureData = await res.json()

    addApiCalls(captureData.formatted)
    console.groupEnd()
    // Your server response structure and key names are what you choose
    if (captureData.error === "INSTRUMENT_DECLINED") {
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