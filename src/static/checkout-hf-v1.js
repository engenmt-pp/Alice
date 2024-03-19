import {
  createOrder,
  getContingencies,
  getStatus,
  captureOrder
} from './checkout.js'

const styles = {
  '.number': {
    'font-family': 'monospace',
  },
  '.valid': { color: 'green' },
  '.invalid': { color: 'red' }
}
const fields = {
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

async function onSubmit(event) {
  event.preventDefault()
  const data = {
    // Cardholder's first and last name
    cardholderName: document.getElementById('card-holder-name').value,
    // Billing Address
    billingAddress: {
      streetAddress: document.getElementById('billing-address-street').value,
      extendedAddress: document.getElementById('billing-address-unit').value,
      region: document.getElementById('billing-address-state').value,
      locality: document.getElementById('billing-address-city').value,
      postalCode: document.getElementById('billing-address-zip').value,
      countryCodeAlpha2: document.getElementById('billing-address-country').value.toUpperCase()
    },
  }
  const contingencies = getContingencies()
  if (contingencies) {
    data.contingencies = contingencies
  }
  await hostedFields.submit()

  console.group("Order approved!")
  await getStatus()
  await captureOrder()
  console.groupEnd()
}
async function loadHostedFields() {
  if (paypal.HostedFields.isEligible()) {
    hostedFields = await paypal.HostedFields.render({
      createOrder,
      fields,
      styles
    })
    const payButton = document.getElementById('pay-button')
    payButton.disabled = false
    document.getElementById('hf-v1-form').onsubmit = onSubmit
  } else {
    alert("Not eligible for hosted fields. Sorry!")
    document.getElementById("hf-v1-form").style = 'display: none'
  }
}

export {
  loadHostedFields as default
}
