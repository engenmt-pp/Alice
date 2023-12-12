/** Get a client token to be included in the JS SDK's script tag for (old) hosted fields. */
async function getClientToken() {
  console.groupCollapsed("Requesting Client token...")

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

  addApiCalls(formatted, click = false)

  console.log(`Client token: ${clientToken}`)
  console.groupEnd()

  return clientToken
}

function hostedFieldsV1Closure() {
  const fields = {
    number: {
      selector: "#hf-v1-card-number",
      placeholder: "4111 1111 1111 1111"
    },
    cvv: {
      selector: "#hf-v1-cvv",
      placeholder: "123"
    },
    expirationDate: {
      selector: "#hf-v1-expiration-date",
      placeholder: "MM/YY"
    }
  }
  const {
    createOrder,
    getStatus,
    captureOrder
  } = checkoutFunctions()
  let hostedFields
  async function onSubmit(event) {
    event.preventDefault()
    await hostedFields.submit({
      // Cardholder's first and last name
      cardholderName: document.getElementById('hf-v1-card-holder-name').value,
      // Billing Address
      billingAddress: {
        streetAddress: document.getElementById('hf-v1-billing-address-street').value,
        extendedAddress: document.getElementById('hf-v1-billing-address-unit').value,
        region: document.getElementById('hf-v1-billing-address-state').value,
        locality: document.getElementById('hf-v1-billing-address-city').value,
        postalCode: document.getElementById('hf-v1-billing-address-zip').value,
        countryCodeAlpha2: document.getElementById('hf-v1-billing-address-country').value.toUpperCase()
      },
      // Trigger 3D Secure authentication
      contingencies: getContingencies()
    })

    console.group("Order approved!")
    await getStatus()
    await captureOrder()
    console.groupEnd()
  }
  async function loadHostedFields() {
    if (paypal.HostedFields.isEligible()) {
      const styles = {
        '.number': {
          'font-family': 'monospace',
        },
        '.valid': { color: 'green' },
        '.invalid': { color: 'red' }
      }
      hostedFields = await paypal.HostedFields.render({
        createOrder,
        fields,
        styles
      })
      const payButton = await document.getElementById('hf-v1-pay')
      payButton.disabled = false
      document.getElementById('form-hf-v1-card').onsubmit = onSubmit
    } else {
      alert("Not eligible for hosted fields. Sorry!")
      document.getElementById("form-hf-v1-card").style = 'display: none'
    }
  }
  return loadHostedFields
}
