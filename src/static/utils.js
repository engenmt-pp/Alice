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

function getPartnerMerchantInfo() {
  const info = {}

  const authHeader = document.getElementById('auth-header')
  if (authHeader != null) {
    info.authHeader = authHeader.value
  }

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
  return { div: div, n: n }
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
        const topLevelNavInput = document.getElementById('input-api-calls')
        if (topLevelNavInput != null) {
          topLevelNavInput.click()
        }
      }
      updateApiCalls()
    }
  }
}