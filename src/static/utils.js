function copyToClipboard(id) {
  // As written, this fails in "production" as the site isn't HTTPS.
  navigator.clipboard.writeText(document.getElementById(id).value)
}


function getOptions() {
  const formData = new FormData(document.getElementById('options-form'))
  const formOptions = Object.fromEntries(formData)
  const partnerMerchantInfo = getPartnerMerchantInfo()
  return {...formOptions, ...partnerMerchantInfo}
}


function getPartnerMerchantInfo() {
  const ids = ['partner-id', 'client-id', 'merchant-id']
  const info = {}
  for (const id of ids) {
    const elt = document.getElementById(id);
    if (elt !== null) {
      info[id] = elt.value
    }
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


function selectTab(event) {
  /**
   * Deactivate all top-level buttons except for the target, and
   * deactivate all top-level divs except the div corresponding to the target.
   */
  const target = event.target
  deactivate('#top-level-buttons button')
  activate(target)

  const divId = target.id.replace('button-', 'tab-')
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
    /**
     * Deactivate all api-call-level buttons except for the target, and
     * deactivate all api-call-level divs except the div corresponding to the target.
     */
    deactivate('#api-calls-buttons button')
    activate(event.target)

    const div = document.getElementById(divId)
    deactivate('#tab-api-calls div')
    activate(div)
  })
  return button
}


function createApiCallDiv(id, contents) {
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

function addApiCalls(formattedCalls, click=true) {
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
        document.getElementById(buttonId).click()
      }
    }
  }
}