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
    deactivate('#div-api-calls div')
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

      const apiCalls = document.getElementById('div-api-calls')
      apiCalls.appendChild(div)

      if (click) {
        document.getElementById('input-api-calls').click()
      }
      // Always illuminate the button!
      document.getElementById(buttonId).click()
    }
  }
}