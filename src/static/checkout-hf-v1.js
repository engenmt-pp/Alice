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

let hostedFields

async function onSubmit(event) {
  event.preventDefault()
  const data = {
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
    const payButton = document.getElementById('hf-v1-pay')
    payButton.disabled = false
    document.getElementById('form-hf-v1-card').onsubmit = onSubmit
  } else {
    alert("Not eligible for hosted fields. Sorry!")
    document.getElementById("form-hf-v1-card").style = 'display: none'
  }
}

export {
  loadHostedFields as default
}
