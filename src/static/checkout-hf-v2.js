import {
  getContingencies,
  createOrder,
  captureOrder,
  createVaultSetupToken,
  createVaultPaymentToken,
  onError
} from './checkout.js'

const style = {
  '.valid': { color: 'green' },
  '.invalid': { color: 'red' }
}

function getMethods() {
  const vaultWithoutPurchase = document.querySelector('#vault-without-purchase:checked')
  if (vaultWithoutPurchase) {
    return {
      createVaultSetupToken,
      onApprove: createVaultPaymentToken,
      onError
    }
  }
  return {
    createOrder,
    onApprove: captureOrder,
    onError
  }
}

let cardFields
async function loadHostedFields() {
  if (cardFields) await cardFields.close()

  const methods = getMethods()
  cardFields = paypal.CardFields({
    style,
    ...methods
  })
  if (cardFields.isEligible()) {
    const nameField = cardFields.NameField()
    await nameField.render('#cardholder-name')

    const numberField = cardFields.NumberField()
    await numberField.render('#card-number')

    const cvvField = cardFields.CVVField()
    await cvvField.render('#cvv')

    const expiryField = cardFields.ExpiryField()
    await expiryField.render('#expiration-date')

    document.querySelector("#hf-v2-form").addEventListener('submit', (event) => {
      event.preventDefault()
      event.stopImmediatePropagation()
      let data = {}
      // const contingencies = getContingencies()
      // console.log('contingencies', contingencies)
      // if (contingencies) {
      //   data.contingencies = contingencies
      // }
      cardFields.submit(data)
    })
  } else {
    alert("Not eligible for Hosted Fields v2!")
  }
}

export {
  loadHostedFields as default
}