function googlePayClosure() {
  const baseRequest = {
    apiVersion: 2,
    apiVersionMinor: 0,
  }
  const {
    createOrder,
    getStatus,
    captureOrder,
  } = checkoutFunctions()
  let
    paymentsClient = null,
    allowedPaymentMethods = null,
    merchantInfo = null
  function getGoogleIsReadyToPayRequest(allowedPaymentMethods) {
    return Object.assign({}, baseRequest, { allowedPaymentMethods })
  }
  async function getGooglePayConfig() {
    if (allowedPaymentMethods == null || merchantInfo == null) {
      const googlePayConfig = await paypal.Googlepay().config()
      console.log("Google Pay Config loaded!", googlePayConfig);
      ({ allowedPaymentMethods, merchantInfo } = googlePayConfig)
    }
    return {
      allowedPaymentMethods,
      merchantInfo,
    }
  }
  async function getGooglePaymentDataRequest() {
    const paymentDataRequest = Object.assign({}, baseRequest)

    const { allowedPaymentMethods, merchantInfo } = await getGooglePayConfig()
    paymentDataRequest.allowedPaymentMethods = allowedPaymentMethods
    paymentDataRequest.merchantInfo = merchantInfo

    paymentDataRequest.transactionInfo = getGoogleTransactionInfo()
    paymentDataRequest.callbackIntents = ["PAYMENT_AUTHORIZATION"]
    return paymentDataRequest
  }
  function getGoogleTransactionInfo() {

    const formOptions = getOptions()
    let displayItems = []
    let totalPrice = 0

    const subtotalPrice = parseFloat(formOptions['item-price'])
    if (subtotalPrice > 0) {
      displayItems.push({
        label: "Subtotal",
        type: "SUBTOTAL",
        price: subtotalPrice.toFixed(2),
      })
      totalPrice += subtotalPrice
    }

    const taxPrice = parseFloat(formOptions['item-tax'])
    if (taxPrice > 0) {
      displayItems.push({
        label: "Tax",
        type: "TAX",
        price: subtotalPrice.toFixed(2),
      })
      totalPrice += taxPrice
    }

    let countryCode = formOptions['buyer-country-code']
    if (countryCode == '') {
      countryCode = 'US'
    }
    const currencyCode = formOptions['currency-code']
    return {
      displayItems,
      countryCode,
      currencyCode,
      totalPriceLabel: "Total",
      totalPriceStatus: "FINAL",
      totalPrice: totalPrice.toFixed(2),
    }
  }
  async function onClick() {
    /**
     * Show Google Pay payment sheet when Google Pay payment button is clicked
     */
    const paymentDataRequest = await getGooglePaymentDataRequest()
    paymentDataRequest.transactionInfo = getGoogleTransactionInfo()

    paymentsClient = getGooglePaymentsClient()
    paymentsClient.loadPaymentData(paymentDataRequest)
  }
  function getGooglePaymentsClient() {
    if (paymentsClient === null) {
      paymentsClient = new google.payments.api.PaymentsClient({
        environment: "TEST",
        paymentDataCallbacks: {
          onPaymentAuthorized: createAndCaptureOrder,
        },
      })
    }
    return paymentsClient
  }
  async function createAndCaptureOrder({ paymentMethodData }) {
    console.group('Creating a PayPal order with paymentMethodData:', paymentMethodData)
    const paymentSource = 'google_pay'
    const options = { paymentSource }
    const orderId = await createOrder(options)
    options.orderID = orderId
    const returnVal = {}
    try {
      console.group("Confirming order with Google...")
      const confirmOrderResponse = await paypal.Googlepay().confirmOrder({
        orderId,
        paymentMethodData
      })
      console.log('Done! confirmOrderResponse:', confirmOrderResponse)
      switch (confirmOrderResponse.status) {
        case "PAYER_ACTION_REQUIRED":
          console.log('Confirmation... requires payer action!')
          const { liabilityShift } = await paypal.Googlepay().initiatePayerAction({ orderId })
          console.log(`liabilityShift: ${liabilityShift}`)
          await getStatus()
        case "APPROVED":
          console.log('Confirmation approved!')
          const captureStatus = await captureOrder(options)
          if (captureStatus === "COMPLETED") {
            console.log("Capture was successful! 😃 Huzzah!")
            returnVal.transactionState = 'SUCCESS'
          } else {
            console.error("Capture was unsuccessful. 😩")
            returnVal.transactionState = 'ERROR'
            returnVal.error = {
              intent: 'PAYMENT_AUTHORIZATION',
              message: 'Transaction failed as "capture order" response status was not "COMPLETED".',
            }
          }
          break
        default:
          console.error('Confirmation NOT approved. 😩')
          returnVal.transactionState = 'ERROR'
          returnVal.error = {
            intent: 'PAYMENT_AUTHORIZATION',
            message: 'Transaction failed as "confirmOrder" response status was not "APPROVED".',
          }
      }
    } catch (err) {
      console.error('Encountered an error:', err)
      returnVal.transactionState = 'ERROR'
      returnVal.error = {
        intent: 'PAYMENT_AUTHORIZATION',
        message: err.message
      }
    } finally {
      console.log('Order complete. returnVal:', returnVal)
      console.groupEnd()
      return returnVal
    }
  }
  async function addGooglePayButton() {
    const buttonOptions = {}

    const buttonColorElt = document.getElementById('google-pay-button-color')
    if (buttonColorElt != null) {
      buttonOptions.buttonColor = buttonColorElt.value.toLowerCase()
    }
    const buttonTypeElt = document.getElementById('google-pay-button-type')
    if (buttonTypeElt != null) {
      buttonOptions.buttonType = buttonTypeElt.value.toLowerCase()
    }

    const buttonLocaleElt = document.getElementById('google-pay-button-locale')
    if (buttonLocaleElt != null) {
      buttonOptions.buttonLocale = buttonLocaleElt.value.toLowerCase()
    }

    paymentsClient = getGooglePaymentsClient()
    const button = paymentsClient.createButton({
      ...buttonOptions,
      onClick,
    })
    document.getElementById("checkout-google-pay").appendChild(button)
  }
  async function onGooglePayLoaded() {
    paymentsClient = getGooglePaymentsClient()
    const { allowedPaymentMethods } = await getGooglePayConfig()
    try {
      const isReadyToPayRequest = getGoogleIsReadyToPayRequest(allowedPaymentMethods)
      const response = await paymentsClient.isReadyToPay(isReadyToPayRequest)
      if (response.result) {
        addGooglePayButton()
      }
    } catch (e) {
      const err = await e.message
      console.error({ err })
    }
  }
  return onGooglePayLoaded
}