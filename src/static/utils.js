function copyToClipboard(id) {
  // As written, this fails in "production" as the site isn't HTTPS.
  navigator.clipboard.writeText(document.getElementById(id).value)
}


function getOptions() {
  const formData = new FormData(document.getElementById('options-form'))
  const formOptions = Object.fromEntries(formData)
  const partnerMerchantInfo = getPartnerMerchantInfo()
  if (typeof authHeader !== 'undefined') {
    partnerMerchantInfo['authHeader'] = authHeader
  }
  return { ...formOptions, ...partnerMerchantInfo }
}


function getPartnerMerchantInfo() {
  const info = {}

  const partnerId = document.getElementById('partner-id')
  if (partnerId != null) {
    info.partnerId = partnerId.value
  }

  const merchantId = document.getElementById('merchant-id')
  if (merchantId != null) {
    info.merchantId = merchantId.value
  }

  const partnerClientId = document.getElementById('partner-client-id')
  if (partnerClientId != null) {
    info.partnerClientId = partnerClientId.value
  }

  const BNCode = document.getElementById('bn-code')
  if (BNCode != null) {
    info.BNCode = BNCode.value
  }
  return info
}


function activate(elt) {
  elt.classList.remove('inactive')
  elt.classList.add('active')
}


function deactivate(selector) {
  document.querySelectorAll(selector).forEach(each => {
    each.classList.remove('active')
    each.classList.add('inactive')
  })
}


function saveOptions(loadHosted = false) {
  const formData = new FormData(document.getElementById('options-form'))
  for (const pair of formData.entries()) {
    window.sessionStorage.setItem(pair[0], pair[1])
  }
  window.sessionStorage.setItem('loadHosted', loadHosted)
}
function loadOptions() {
  const keys = Object.keys(window.sessionStorage)
  const options = {}
  for (const key of keys) {
    const val = window.sessionStorage.getItem(key)
    if (key !== 'loadHosted') {
      document.getElementById(key).value = val
    }
    options[key] = val
  }
  return options
}


function selectTabHostedClosure() {
  function saveAndReload() {
    saveOptions(loadHosted = true)
    location.reload()
  }
  function activateAndRenderHostedFields() {
    /** This is attached to the top-level "Checkout - Hosted Fields" button.
     * It deactivates all top-level nav buttons except for the target and
     * deactivates all top-level divs except the div corresponding to the target.
     */
    const buttonHostedFields = document.getElementById('button-checkout-hosted')
    deactivate('#top-level-buttons button')
    activate(buttonHostedFields)

    const renderHostedFields = hostedFieldsClosure()
    buildScriptElement(renderHostedFields, hosted = true)
    addOnChange(saveAndReload)

    const divIdHostedFields = buttonHostedFields.id.replace('button-', 'tab-')
    const divHostedFields = document.getElementById(divIdHostedFields)
    deactivate('#top-level-nav ~ div')
    activate(divHostedFields)
  }
  function loadHostedFields(event) {
    const hostedFieldCardNumber = document.getElementById('braintree-hosted-field-number')
    if (hostedFieldCardNumber != null) {
      /** The 'braintree-hosted-field-number' iframe exists in the DOM,
       * so we'll have to reload the page to re-render the hosted fields.
       */
      saveAndReload()
    } else {
      activateAndRenderHostedFields()
    }
  }
  return loadHostedFields
}

function selectTab(event) {
  /** This is attached to the top-level "Checkout - Branded" and "API Calls" buttons.
   * It deactivates all top-level nav buttons except for the target and
   * deactivates all top-level divs except the div corresponding to the target.
   */

  const target = event.target
  const target_id = target.id
  const curr = document.querySelector('#top-level-buttons .active')
  let curr_id
  if (curr != null) {
    curr_id = curr.id
  }

  deactivate('#top-level-buttons button')
  activate(target)

  if (target_id.includes('branded') || target_id.includes('card')) {
    if (curr_id == null || curr_id.includes('hosted')) {
      const loadCheckout = brandedAndCardFieldsClosure()
      buildScriptElement(loadCheckout)
      addOnChange(() => {
        buildScriptElement(loadCheckout)
      })
    }
  }

  const divId = target_id.replace('button-', 'tab-')
  const div = document.getElementById(divId)
  deactivate('#top-level-nav ~ div')
  activate(div)
}


function createApiCallButton(id, divId) {
  const button = document.createElement('button')
  button.type = 'button'

  let n = 1
  let buttonId = `button-${id}-${n}`
  while (document.getElementById(buttonId)) {
    n++
    buttonId = `button-${id}-${n}`
  }
  button.id = buttonId

  let title
  if (n === 1) {
    title = id
  } else {
    title = `${id} (${n})`
  }
  button.innerHTML = title
  button.classList.add('inactive')
  button.addEventListener('click', (event) => {
    // Deactivate all api-call-level buttons except for the target.
    deactivate('#api-calls-buttons button')
    activate(event.target)

    // Also deactivate all api-call-level divs except the div corresponding to the target.
    const div = document.getElementById(divId)
    deactivate('#tab-api-calls div')
    activate(div)
  })
  return button
}


function createApiCallDiv(id, contents) {
  if (id === 'access-token') {
    const prevElt = document.getElementById(id)
    if (prevElt != null) {
      prevElt.remove()
    }
  }
  const div = document.createElement('div')

  let n = 1
  let divId = `${id}-${n}`
  while (document.getElementById(divId)) {
    n++
    divId = `${id}-${n}`
  }
  div.id = divId

  div.innerHTML = contents
  div.classList.add('api-response')
  return div
}

function addApiCalls(formattedCalls, click = true) {
  const apiCallsButtons = document.getElementById('api-calls-buttons')
  for (const id in formattedCalls) {
    if (formattedCalls.hasOwnProperty(id)) {
      // `id` is something like 'create-order'.
      let contents = formattedCalls[id]
      const div = createApiCallDiv(id, contents)

      const li = document.createElement('li')
      const button = createApiCallButton(id, div.id)
      const buttonId = button.id
      li.appendChild(button)
      apiCallsButtons.appendChild(li)

      const apiCalls = document.getElementById('tab-api-calls')
      apiCalls.appendChild(div)

      if (click) {
        document.getElementById('button-api-calls').click()
      }
      // Always illuminate the button!
      document.getElementById(buttonId).click()
    }
  }
}