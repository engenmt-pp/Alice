function saveOptions() {
  const formData = new FormData(document.getElementById('options-form'))
  for (const pair of formData.entries()) {
    if (pair[0] != 'auth-header') {
      window.sessionStorage.setItem(pair[0], pair[1])
    }
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
function getOptions() {
  const formData = new FormData(document.getElementById('options-form'))
  const formOptions = Object.fromEntries(formData)
  const partnerMerchantInfo = getPartnerMerchantInfo()
  return { ...formOptions, ...partnerMerchantInfo }
}
function setOptions(options) {
  for (const [key, value] of Object.entries(options)) {
    const element = document.getElementById(key)
    if (element != null) {
      element.value = value
    }
  }
}

function getAuthHeader() {
  const elementAuthHeader = document.getElementById('auth-header')
  if (elementAuthHeader == null) {
    return elementAuthHeader
  }
  return elementAuthHeader.value
}
function setAuthHeader(authHeader) {
  document.getElementById('auth-header').value = authHeader
}

function getPartnerMerchantInfo() {
  const info = {}

  const authHeader = getAuthHeader()
  if (authHeader != null) {
    info['auth-header'] = authHeader
  }

  const partnerId = document.getElementById('partner-id')
  if (partnerId != null) {
    info['partner-id'] = partnerId.value
  }

  const partnerClientId = document.getElementById('partner-client-id')
  if (partnerClientId != null) {
    info['partner-client-id'] = partnerClientId.value
  }

  const partnerSecret = document.getElementById('partner-secret')
  if (partnerSecret != null) {
    info['partner-secret'] = partnerSecret.value
  }

  const BNCode = document.getElementById('partner-bn-code')
  if (BNCode != null) {
    info['partner-bn-code'] = BNCode.value
  }

  const merchantId = document.getElementById('merchant-id')
  if (merchantId != null) {
    info['merchant-id'] = merchantId.value
  }

  return info
}

function saveOptionsAndReloadPage() {
  saveOptions()
  console.log(JSON.stringify(window.sessionStorage, null, 2))
  location.reload()
}

function activate(element) {
  element.classList.remove('inactive')
  element.classList.add('active')
}
function deactivate(element) {
  element.classList.remove('active')
  element.classList.add('inactive')
}

function changeTopLevelNav() {
  const nav = document.getElementById('top-level-nav')
  const checkedInput = nav.querySelector('input:checked')
  const checkedInputId = checkedInput.getAttribute('id')
  const activeDivId = checkedInputId.replace('input', 'div')

  nav.querySelectorAll('input').forEach((each) => {
    const inputId = each.getAttribute('id').replace('input', 'div')
    const divId = inputId.replace('input', 'div')
    const div = document.getElementById(divId)
    if (divId == activeDivId) {
      activate(div)
    } else {
      deactivate(div)
    }
  })
}


function updateApiCalls() {
  /* This event fires when an input in #div-api-calls > nav gets checked.
   */
  const apiCalls = document.getElementById('div-api-calls')
  const checkedInput = apiCalls.querySelector('input:checked')
  const checkedInputId = checkedInput.getAttribute('id')
  const divId = checkedInputId.replace('input', 'div')
  const divElement = document.getElementById(divId)

  apiCalls.querySelectorAll('div').forEach(deactivate)
  activate(divElement)
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
  return { div, n }
}
function createApiCallInput(baseId, n) {
  const input = document.createElement('input')
  input.setAttribute('type', 'radio')
  input.setAttribute('name', 'api-calls-nav-tabs')
  input.setAttribute('checked', true)

  const inputId = `input-api-call-${baseId}-${n}`
  input.setAttribute('id', inputId)
  input.onchange = updateApiCalls

  return input
}
function createApiCallDownloadButton(baseId, curl) {
  const button = document.createElement('button')
  button.innerHTML = 'Download for Postman'
  button.style.display = 'block'
  button.classList.add('action')
  button.classList.add('postman')
  button.setAttribute('type', 'button')

  const fileName = `${baseId}.txt`
  button.onclick = function () {
    const elt = document.createElement('a')
    const href = 'data:text/plain;charset=utf-8,' + encodeURIComponent(curl)
    console.log('href:', href)
    elt.setAttribute('href', href)
    elt.setAttribute('download', fileName)
    elt.click()
  }

  return button
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
      const { human, curl } = formattedCalls[baseId]
      const { div, n } = createApiCallDiv(baseId, human)
      const button = createApiCallDownloadButton(baseId, curl)
      div.prepend(button)
      apiCalls.append(div)

      const input = createApiCallInput(baseId, n)
      apiCallsNav.append(input)

      const inputId = input.getAttribute('id')
      const label = createApiCallLabel(baseId, inputId, n)
      apiCallsNav.append(label)

      if (click) {
        const topLevelNavInput = document.getElementById('input-api-calls')
        if (topLevelNavInput != null) {
          topLevelNavInput.click()
        }
      }
      updateApiCalls()
    }
  }
}

function downloadAll() {
  document.querySelectorAll('#div-api-calls button').forEach((button) => { button.click() })
}

function resetPartnerInfo() {
  const fieldset = document.getElementById('partner-merchant-credentials')
  fieldset.querySelectorAll('input').forEach((input) => {
    input.value = input.defaultValue
  })
}