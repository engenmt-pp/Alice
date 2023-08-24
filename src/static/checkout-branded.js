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
        const vaultWithoutPurchase = document.getElementById('vault-without-purchase')
        if (vaultWithoutPurchase.checked) {
            methods = {
                onClick: onClick,
                createVaultSetupToken: createVaultSetupToken,
                onApprove: createVaultPaymentToken
            }
        } else {
            methods = {
                onClick: onClick,
                createOrder: createOrder,
                onApprove: captureOrder
            }
        }
        buttons = await paypal.Buttons(methods)
        return buttons
            .render("#paypal-button-container")
            .catch((err) => {
                console.log('Caught an error while rendering checkout:', err)
            })
    }
    return loadButtons
}