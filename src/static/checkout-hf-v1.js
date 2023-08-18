/** Get a client token to be included in the JS SDK's script tag for (old) hosted fields. */
async function getClientToken() {
  console.groupCollapsed("Requesting Client token...")

  const endpoint = "/api/identity/client-token"
  const clientTokenResponse = await fetch(endpoint, {
    headers: { "Content-Type": "application/json" },
    method: "POST"
  })
  const clientTokenData = await clientTokenResponse.json()
  const { formatted, clientToken } = clientTokenData

  addApiCalls(formatted, click = false)

  console.log(`Client token: ${clientToken}`)
  console.groupEnd()

  return clientToken
}

function getContingencies() {
  return [document.getElementById('3ds-preference').value]
}

function hostedFieldsV1Closure() {
  const fields = {
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
  const styles = {
    '.number': {
      'font-family': 'monospace',
    },
    '.valid': { 'color': 'green' },
    '.invalid': { 'color': 'red' }

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
        styles: styles
      })
      const payButton = await document.getElementById('hf-pay')
      payButton.disabled = false
      document.getElementById('form-hf-card').onsubmit = onSubmit
    } else {
      alert("Not eligible for hosted fields. Sorry!")
      document.getElementById("form-hf-card").style = 'display: none'
    }
  }
  return loadHostedFields
}
