import {
    onClick,
    createOrder,
    captureOrder,
    createVaultSetupToken,
    createVaultPaymentToken
} from './checkout.js'

function getMethods() {
    const vaultWithoutPurchase = document.querySelector('#vault-without-purchase:checked')
    if (vaultWithoutPurchase) {
        return {
            onClick,
            createVaultSetupToken,
            onApprove: createVaultPaymentToken
        }
    }
    return {
        onClick,
        createOrder,
        onApprove: captureOrder
    }
}

function getStyle() {
    const label = document.getElementById('button-label')?.value
    if (label) {
        return { label }
    }
    return {}
}

let buttons
async function loadButtons() {
    if (buttons != null) await buttons.close()
    const style = getStyle()
    const methods = getMethods()
    buttons = await paypal.Buttons({
        style,
        ...methods
    })
    return buttons
        .render("#paypal-button-container")
        .catch((err) => {
            console.log('Caught an error while rendering PayPal buttons:', err)
        })
}

export {
    loadButtons as default
}