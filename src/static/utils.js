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
    if (element) {
      if (element.getAttribute('type') === 'checkbox') {
        element.checked = true
      } else {
        element.value = value
      }
    }
  }
}

function setAuthHeader(authHeader) {
  document.getElementById('auth-header').value = authHeader
}

function getPartnerMerchantInfo() {
  const ids = ['auth-header', 'partner-id', 'client-id', 'secret', 'bn-code', 'merchant-id']
  const info = {}
  ids.forEach((id) => {
    const value = document.getElementById(id)?.value
    if (value) info[id] = value
  })
  return info
}

function saveOptionsAndReloadPage(togglePpcp = false) {
  const currentPpcpType = document.querySelector('#partner-id') ? 'partner' : 'merchant'
  let ppcpType
  if (togglePpcp) {
    console.log(`Toggling ppcpType from ${currentPpcpType} to...`)
    ppcpType = (currentPpcpType == 'merchant') ? 'partner' : 'merchant' // Sorry in advance
    console.log(`...${ppcpType}`)
  } else {
    ppcpType = currentPpcpType
  }
  saveOptions()
  console.log(JSON.stringify(window.sessionStorage, null, 2))
  const newUrl = new URL(window.location.href)
  newUrl.searchParams.set('ppcpType', ppcpType)
  window.location = newUrl.href
}

function createTabPanel(contents) {
  const div = document.createElement('div')
  div.setAttribute('role', 'tabpanel')
  div.innerText = contents
  div.classList.add('api-response')

  return div
}
function createDownloadButton(label, curl) {
  const button = document.createElement('button')
  button.innerHTML = 'Download for Postman'
  button.style.display = 'block'
  button.classList.add('postman')
  button.setAttribute('data-method', '')
  button.setAttribute('type', 'button')

  const fileName = `${label}.txt`
  button.onclick = function () {
    const elt = document.createElement('a')
    const href = 'data:text/plain;charset=utf-8,' + encodeURIComponent(curl)
    elt.setAttribute('href', href)
    elt.setAttribute('download', fileName)
    elt.click()
  }

  return button
}
function createTab(label) {
  const button = document.createElement('button')
  button.setAttribute('role', 'tab')
  button.innerText = label

  return button
}

function addApiCalls(formattedCalls, click = true) {
  const theTabs = document.querySelector('the-tabs the-tabs')
  const apiCallsTabList = document.querySelector('[role=tabpanel] [role=tablist]')
  for (const label in formattedCalls) {
    if (formattedCalls.hasOwnProperty(label)) {
      // `label` is something like 'create-order'.
      const { human, curl } = formattedCalls[label]
      const tabPanel = createTabPanel(human)
      const downloadButton = createDownloadButton(label, curl)
      tabPanel.prepend(downloadButton)
      theTabs.append(tabPanel) // `tabPanel` is the last child of `theTabs`

      const tab = createTab(label)
      apiCallsTabList.append(tab)
    }
  }
  theTabs.setupEvents()
  const lastTab = apiCallsTabList.querySelector(':last-child')
  if (lastTab) {
    lastTab.click()
  }
  if (click) {
    document.getElementById('tab-api-calls').click()
  }
}

function downloadAll() {
  document.querySelectorAll('[role=tabpanel] [role=tabpanel] button').forEach((button) => { button.click() })
}

function setupCredentials() {
  document.querySelectorAll('#credentials > input').forEach((elt) => {
    elt.addEventListener('change', () => { setAuthHeader('') })
  })
  document.getElementById('button-edit').onclick = allowCredentialEditing

  document.getElementById('download-all')?.addEventListener('click', downloadAll)
}

function resetCredentials() {
  setAuthHeader('')
  const credentials = document.getElementById('credentials')
  credentials.querySelectorAll('input').forEach((elt) => {
    elt.value = elt.defaultValue
    elt.dispatchEvent(new Event('change'))
  })
}

function allowCredentialEditing() {
  const credentials = document.getElementById('credentials')
  credentials.querySelectorAll('input:disabled').forEach((input) => {
    input.disabled = false
  })
  credentials.querySelector('input').focus()

  const button = credentials.getElementById('button-edit')
  button.onclick = resetCredentials
  button.innerHTML = 'Reset'
}

function togglePpcp() {

  const ppcpType = localStorage.getItem('ppcpType') ?? 'partner'
}

export {
  saveOptions,
  setOptions,
  getOptions,
  loadOptions,
  setAuthHeader,
  getPartnerMerchantInfo,
  saveOptionsAndReloadPage,
  addApiCalls,
  setupCredentials,
}