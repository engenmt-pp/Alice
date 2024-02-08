import {
  saveOptionsAndReloadPage
} from './utils.js'

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

let cardFields
async function loadHostedFieldsV2() {
  if (cardFields) {
    /* We've been instructed to load the hosted fields, but they're already loaded.
     * We'll just save the user's options and reload the page.
     */
    saveOptionsAndReloadPage()
  }

  let methods
  const vaultWithoutPurchase = document.getElementById('vault-without-purchase')
  if (vaultWithoutPurchase.checked) {
    methods = {
      createVaultSetupToken,
      onApprove: createVaultPaymentToken,
      onError
    }
  } else {
    methods = {
      createOrder,
      onApprove: captureOrder,
      onError
    }
  }
  cardFields = paypal.CardFields({
    style,
    ...methods
  })
  if (cardFields.isEligible()) {
    const nameField = cardFields.NameField()
    await nameField.render('#hf-v2-card-holder-name')

    const numberField = cardFields.NumberField()
    await numberField.render('#hf-v2-card-number')

    const cvvField = cardFields.CVVField()
    await cvvField.render('#hf-v2-cvv')

    const expiryField = cardFields.ExpiryField()
    await expiryField.render('#hf-v2-expiration-date')

    document.querySelector("#form-hf-v2-card").addEventListener('submit', (event) => {
      event.preventDefault()
      event.stopImmediatePropagation()
      const contingencies = getContingencies()
      let data
      if (contingencies) {
        data = { contingencies }
      } else {
        data = {}
      }
      cardFields.submit(data)
    })
  } else {
    alert("Not eligible for Hosted Fields v2!")
  }
}

export {
  loadHostedFieldsV2 as default
}