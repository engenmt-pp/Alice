function googlePayClosure() {
  const baseRequest = {
    apiVersion: 2,
    apiVersionMinor: 0,
  }
  const {
    createOrder,
    captureOrder,
  } = checkoutFunctions()
  let
    paymentsClient = null,
    allowedPaymentMethods = null,
    merchantInfo = null
  function getGoogleIsReadyToPayRequest(allowedPaymentMethods) {
    return Object.assign({}, baseRequest, { allowedPaymentMethods: allowedPaymentMethods })
  }
  async function getGooglePayConfig() {
    if (allowedPaymentMethods == null || merchantInfo == null) {
      const googlePayConfig = await paypal.Googlepay().config()
      console.log("Google Pay Config loaded!", googlePayConfig)
      allowedPaymentMethods = googlePayConfig.allowedPaymentMethods
      merchantInfo = googlePayConfig.merchantInfo
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
  async function createAndCaptureOrder(paymentData) {
    console.group('Creating a PayPal order with paymentData:', paymentData)
    const paymentSource = 'google_pay'
    const options = { paymentSource }
    const orderId = await createOrder(options)
    options.orderID = orderId
    const returnVal = {}
    try {
      console.group("Confirming order with Google...")
      const confirmOrderResponse = await paypal.Googlepay().confirmOrder({
        orderId: orderId,
        paymentMethodData: paymentData.paymentMethodData
      })
      console.log('Done! confirmOrderResponse:', confirmOrderResponse)
      if (confirmOrderResponse.status === "APPROVED") {
        console.log('Confirmation approved!')
        const captureStatus = await captureOrder(options)
        if (captureStatus === "COMPLETED") {
          console.log("Capture was successful! 😃 Huzzah!")
          returnVal.transactionState = 'SUCCESS'
        } else {
          console.log("Capture was unsuccessful. 😩")
          returnVal.transactionState = 'ERROR'
          returnVal.error = {
            intent: 'PAYMENT_AUTHORIZATION',
            message: 'TRANSACTION FAILED AS CAPTURE STATUS WAS NOT COMPLETED.',
          }
        }
      } else {
        console.error('Confirmation NOT approved. 😩')
        returnVal.transactionState = 'ERROR'
        returnVal.error = {
          intent: 'PAYMENT_AUTHORIZATION',
          message: 'TRANSACTION FAILED AS CONFIRM ORDER RESPONSE STATUS WAS NOT APPROVED',
        }
      }
    } catch (err) {
      console.error('Encountered an error:', err)
      returnVal.transactionState =
        'ERROR'
      returnVal.error = {
        intent: 'PAYMENT_AUTHORIZATION',
        message: err.message
      }
    } finally {
      console.log('Done. returnVal:', returnVal)
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