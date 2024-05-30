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

async function onSubmit(event) {
  event.preventDefault()
  event.stopImmediatePropagation()

  const { id: paymentTokenId } = await fastlanePaymentComponent.getPaymentToken()

  if (paymentTokenId) {
    console.log('Received paymentTokenId:', paymentTokenId)
    await attemptOrder(paymentTokenId)
  } else {
    console.log('Failed to receive paymentTokenId!')
  }
}

async function attemptOrder(paymentTokenId) {
  const { orderId, authId, captureId } = await createOrder(paymentTokenId)

  if (captureId) {
    console.log(`Received capture back from 'create order': ${captureId}`)
    return
  } else {
    console.log('Attempting capture...')
    await captureOrder({ orderId, authId })
  }
}

async function loadFastlane() {
  fastlane = await paypal.Fastlane()
  console.log(fastlane)

  window.localStorage.setItem('fastlaneEnv', 'sandbox')

  fastlanePaymentComponent = await fastlane.FastlanePaymentComponent()
  fastlanePaymentComponent.render("#payment-container")

  const fastlaneForm = document.getElementById("fastlane-form")
  fastlaneForm.addEventListener("submit", onSubmit)
}

export {
  loadFastlane as default
}