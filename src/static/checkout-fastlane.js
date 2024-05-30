// import {
//   captureOrder,
//   createOrder,
// } from './checkout.js'
import {
    addApiCalls,
    getOptions,
    setAuthHeader
} from './utils.js'

let fastlane
let fastlanePaymentComponent
let identity, profile

async function createOrder(singleUseToken) {
    console.group("Creating the order...")

    const options = getOptions()
    if (singleUseToken) {
        options['single-use-token'] = singleUseToken
        options['payment-source'] = 'card'
    } else {
        alert('No singleUseToken received!')
        return
    }

    const createResp = await fetch("/api/orders/", {
        headers: { "Content-Type": "application/json" },
        method: "POST",
        body: JSON.stringify(options),
    })
    const createData = await createResp.json()
    const {
        formatted,
        authHeader,
        orderId,
        authId,
        authStatus,
        captureId,
        captureStatus,
    } = createData
    setAuthHeader(authHeader)

    addApiCalls(formatted)
    console.log(`Order ${orderId} created!`)
    if (captureId) {
        console.log(`Capture ${captureId} was ${captureStatus}!`)
    } else {
        console.log(`Authorization ${authId} was ${authStatus}!`)
    }
    console.groupEnd()
    return { orderId, authId, captureId }
}

async function captureOrder({ orderId, authId }) {
    const options = getOptions()
    options['payment-source'] = 'card'

    if (authId) {
        console.group(`Capturing authorization ${authId}...`)
        options['auth-id'] = authId
    } else {
        console.group(`Capturing order ${orderId}...`)
    }

    const captureResp = await fetch(`/api/orders/${orderId}/capture`, {
        headers: { 'Content-Type': 'application/json' },
        method: 'POST',
        body: JSON.stringify(options)
    })

    const captureData = await captureResp.json()
    const { formatted, authHeader, captureStatus } = captureData
    setAuthHeader(authHeader)
    if (captureStatus) {
        console.log(`Captured order ${orderId}! Capture status: ${captureStatus}`)
    } else {
        console.log(`Unable to capture order.`)
    }

    addApiCalls(formatted)
    console.groupEnd()
}


async function attemptCheckout() {
    if (fastlanePaymentComponent) {
        facilitateCheckout()
    } else {
        alert("Need to look up an email first!")
    }
}
async function facilitateCheckout() {
    console.log("Facilitating checkout...")
    const { id: paymentTokenId } = await fastlanePaymentComponent.getPaymentToken()

    const { orderId, authId, captureId } = await createOrder(paymentTokenId)

    if (captureId) {
        console.log(`Received capture back from 'create order': ${captureId}`)
    } else {
        console.log('Attempting capture...')
        await captureOrder({ orderId, authId })
    }
}

async function setUpCheckout() {
    const emailContainer = document.getElementById('fastlane-email-container')
    const emailButton = document.getElementById('fastlane-email-button')

    const emailInput = document.getElementById('fastlane-email-input')
    const emailAddress = emailInput?.value

    if (emailAddress) {
        emailContainer.setAttribute('hidden', true)
        emailContainer.setAttribute('disabled', true)
        emailInput.setAttribute('disabled', true)
        emailButton.classList.toggle('disabled')

        const {
            customerContextId
        } = await identity.lookupCustomerByEmail(emailAddress)

        if (customerContextId) {
            await setUpReturnBuyerCheckout(customerContextId)
        } else {
            await setUpGuestBuyerCheckout()
        }
    } else {
        alert('No email found to look up!')
    }

    if (fastlanePaymentComponent) {
        await fastlanePaymentComponent.render('#payment-container')

        const fastlaneWatermark = document.getElementById('watermark-container')
        fastlaneWatermark.classList.toggle('hidden')

        const payButton = document.getElementById('pay-button')
        payButton.classList.toggle('disabled')
    }
}

async function setUpReturnBuyerCheckout(customerContextId) {
    console.group('Facilitating return buyer (Ryan) flow...')
    console.log('customerContextId:', customerContextId)

    const {
        authenticationState,
        profileData
    } = await identity.triggerAuthenticationFlow(customerContextId)
    console.log('Authentication result:', { authenticationState, profileData })
    if (authenticationState === 'succeeded') {
        console.log("Authentication succeeded! profileData:", profileData)
        const { shippingAddress } = profileData
        if (shippingAddress) {
            displayShippingAddress(shippingAddress)
        } else {
            alert('No shipping address!')
        }
        fastlanePaymentComponent = await fastlane.FastlanePaymentComponent()
    } else {
        console.log("Authentication unsuccessful... falling back to guest experience.")
        console.groupEnd()
        return await setUpGuestBuyerCheckout()
    }
    console.groupEnd()
}

async function setUpGuestBuyerCheckout() {
    console.group('Facilitating guest buyer (Gary) flow...')

    const fields = {
        phoneNumber: { prefill: "8882211161" },
        cardholderName: { prefill: "Noauthgary Cardholder" }
    }
    const shippingAddress = {
        firstName: "Comp",
        lastName: "Smith",
        streetAddress: "1 East 1st St",
        extendedAddress: "5th Floor",
        locality: "Bartlett",
        region: "IL", //must be sent in 2-letter format
        postalCode: "60103",
        countryCodeAlpha2: "US"
    }

    fastlanePaymentComponent = await fastlane.FastlanePaymentComponent({ fields, shippingAddress })
    console.groupEnd()
}

async function displayShippingAddress(shippingAddress) {
    const { name, address, phoneNumber } = shippingAddress

    const container = document.getElementById('shipping-address-container')
    container.innerHTML = '<span>Shipping Address</span>'

    if (name) container.append(`\n${name.fullName}`)

    if (address) {
        const {
            addressLine1 = 'addressLine1',
            addressLine2,
            adminArea1 = 'adminArea1',
            adminArea2 = 'adminArea2',
            postalCode = 'postalCode'
        } = address

        container.append(`\n${addressLine1}`)

        if (addressLine2) container.append(`\n${addressLine2}\n`)

        container.append(`\n${adminArea2}, ${adminArea1} ${postalCode}\n`)
    }

    if (phoneNumber) {
        const {
            countryCode = 'countryCode',
            nationalNumber = 'nationalNumber'
        } = phoneNumber
        container.append(`\n+${countryCode} ${nationalNumber}\n`)
    }
}

async function loadFastlane() {
    fastlane = await paypal.Fastlane()
    console.log('Fastlane:', fastlane);
    ({ identity, profile } = fastlane)

    const fastlaneWatermark = await fastlane.FastlaneWatermarkComponent({
        includeAdditionalInfo: true
    })
    fastlaneWatermark.render('#watermark-container')

    window.localStorage.setItem('fastlaneEnv', 'sandbox')

    const emailLookupButton = document.getElementById('fastlane-email-button')
    emailLookupButton.addEventListener('click', setUpCheckout)
    emailLookupButton.classList.toggle('disabled')

    document.getElementById('pay-button').addEventListener('click', attemptCheckout)

}

export {
    loadFastlane as default
}