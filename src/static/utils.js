function getOptions() {
  const formData = new FormData(document.getElementById('options-form'))
  const formOptions = Object.fromEntries(formData)
  const partnerMerchantInfo = getPartnerMerchantInfo()
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

function saveOptions() {
  const formData = new FormData(document.getElementById('options-form'))
  for (const pair of formData.entries()) {
    window.sessionStorage.setItem(pair[0], pair[1])
  }
}
function loadOptions() {
  const keys = Object.keys(window.sessionStorage)
  const options = {}
  for (const key of keys) {
    const val = window.sessionStorage.getItem(key)
    options[key] = val
  }
  return options
}

function saveOptionsAndReloadPage() {
  saveOptions()
  location.reload()
}

function updateApiCalls() {
  /* This event fires when an input in #div-api-calls > nav gets checked.
   */
  const apiCalls = document.querySelector('#div-api-calls')
  const targetInput = apiCalls.querySelector('input[checked]')
  const targetInputId = targetInput.getAttribute('id')
  const divId = targetInputId.replace('input', 'div')
  const divElement = document.getElementById(divId)

  apiCalls.querySelectorAll('div').forEach((each) => {
    each.classList.remove('active')
    each.classList.add('inactive')
  })

  divElement.classList.remove('inactive')
  divElement.classList.add('active')
}
function createApiCallDiv(baseId, contents) {
  const div = document.createElement('div')

  let n = 1
  let divId = `div-api-call-${baseId}-${n}`
  while (document.getElementById(divId)) {
    n++
    divId = `div-api-call-${baseId}-${n}`
  }
  div.setAttribute('id', divId)
  div.innerText = contents
  div.classList.add('api-response')
  return { div: div, n: n }
}
function createApiCallInput(baseId, n) {
  const input = document.createElement('input')
  input.setAttribute('type', 'radio')
  input.setAttribute('name', 'api-calls-nav-tabs')

  const inputId = `input-api-call-${baseId}-${n}`
  input.setAttribute('id', inputId)
  input.onchange = updateApiCalls
  // input.setAttribute('onchange', 'updateApiCalls')

  return input
}
function createApiCallLabel(baseId, inputId, n) {
  const label = document.createElement('label')
  label.setAttribute('for', inputId)
  let title = baseId
  if (n > 1) {
    title += ` (${n})`
  }
  label.innerText = title

  return label
}

function addApiCalls(formattedCalls, click = true) {
  const apiCalls = document.getElementById('div-api-calls')
  const apiCallsNav = apiCalls.querySelector('nav')
  for (const baseId in formattedCalls) {
    if (formattedCalls.hasOwnProperty(baseId)) {
      // `baseId` is something like 'create-order'.
      let contents = formattedCalls[baseId]
      const { div, n } = createApiCallDiv(baseId, contents)
      apiCalls.appendChild(div)

      const input = createApiCallInput(baseId, n)
      apiCallsNav.appendChild(input)

      const inputId = input.getAttribute('id')
      const label = createApiCallLabel(baseId, inputId, n)
      apiCallsNav.appendChild(label)

      if (click) {
        document.getElementById('input-api-calls').click()
      }
      input.setAttribute('checked', true)
      updateApiCalls()
    }
  }
}