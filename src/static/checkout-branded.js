function brandedClosure() {
    const {
        onClick,
        createOrder,
        captureOrder,
        createVaultSetupToken,
        createVaultPaymentToken
    } = checkoutFunctions()
    let buttons
    async function loadButtons() {
        if (buttons != null) await buttons.close()
        let methods
        const vaultWithoutPurchase = document.querySelector('#vault-without-purchase:checked')
        if (vaultWithoutPurchase) {
            methods = {
                onClick,
                createVaultSetupToken,
                onApprove: createVaultPaymentToken
            }
        }
        else {
            methods = {
                onClick,
                createOrder,
                onApprove: captureOrder
            }
        }
        let style = {}
        const buttonLabelElement = document.getElementById('button-label')
        if (buttonLabelElement != null && buttonLabelElement.value != '') {
            style.label = buttonLabelElement.value
        }
        buttons = await paypal.Buttons({
            style,
            ...methods
        })
        return buttons
            .render("#paypal-button-container")
            .catch((err) => {
                console.log('Caught an error while rendering checkout:', err)
            })
    }
    return loadButtons
}