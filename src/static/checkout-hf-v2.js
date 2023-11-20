function hostedFieldsV2Closure() {
  const {
    createOrder,
    captureOrder,
    createVaultSetupToken,
    createVaultPaymentToken,
    onError
  } = checkoutFunctions()
  let cardFields
  async function loadHostedFieldsV2() {
    if (cardFields != null) {
      saveOptionsAndReloadPage()
    }
    let methods
    const vaultWithoutPurchase = document.getElementById('vault-without-purchase')
    if (vaultWithoutPurchase.checked) {
      methods = {
        createVaultSetupToken: createVaultSetupToken,
        onApprove: createVaultPaymentToken,
        onError: onError
      }
    } else {
      methods = {
        createOrder,
        onApprove: captureOrder,
        onError
      }
    }
    const style = {
      '.valid': { color: 'green' },
      '.invalid': { color: 'red' },
      'input': { padding: '10px' }
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
        cardFields.submit()
      })
    } else {
      alert("Not eligible for Hosted Fields v2!")
    }
  }
  return loadHostedFieldsV2
}