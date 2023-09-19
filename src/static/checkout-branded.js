function brandedClosure() {
    const {
        onError,
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
        if (vaultWithoutPurchase != null) {
            methods = {
                onClick: onClick,
                createVaultSetupToken: createVaultSetupToken,
                onApprove: createVaultPaymentToken
            }
        } else {
            methods = {
                onError,
                onClick: onClick,
                createOrder: createOrder,
                onApprove: captureOrder
            }
        }
        let style = {}
        const buttonLabelElement = document.getElementById('button-label')
        if (buttonLabelElement != null && buttonLabelElement.value != '') {
            style.label = buttonLabelElement.value
        }
        buttons = await paypal.Buttons({ ...methods, style: style })
        return buttons
            .render("#paypal-button-container")
            .catch((err) => {
                console.log('Caught an error while rendering checkout:', err)
            })
    }
    return loadButtons
}