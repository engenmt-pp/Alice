function copyToClipboard(id) {
  navigator.clipboard.writeText(document.getElementById(id).value)
}

function updateAPICalls(formattedCalls, click=true) {
  const apiCallsButton = document.getElementById('api-calls')
  if (click) {
    apiCallsButton.click()
  }
  for (const id in formattedCalls) {
    if (formattedCalls.hasOwnProperty(id)) {
      const contents = formattedCalls[id]
      const apiResponseDiv = document.getElementById(id)
      apiResponseDiv.innerHTML = contents
      const apiResponseButton = document.getElementById(`button-${id}`)
      enableButton(apiResponseButton)
      if (click) {
        apiResponseButton.click()
      }
    }
  }
}

function addApiCalls(formattedCalls, click=true) {
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
      document.querySelectorAll('#api-calls button').forEach(each => {
        each.classList.remove('active')
        each.classList.add('inactive')
      })
      event.target.classList.add('active')

      const divList = document.querySelectorAll('#api-calls div')
      divList.forEach(each => {
        each.classList.remove('active')
        each.classList.add('inactive')
      })
      document.getElementById(divId).classList.remove('inactive')
      document.getElementById(divId).classList.add('active')
    })

    return button
  }

  const apiCallsButtons = document.getElementById('buttons-api-calls')
  for (const id in formattedCalls) {
    if (formattedCalls.hasOwnProperty(id)) {
      let contents = formattedCalls[id]
      const div = createApiCallDiv(id, contents)

      const li = document.createElement('li')
      const button = createApiCallButton(id, div.id)
      const buttonId = button.id
      li.appendChild(button)
      apiCallsButtons.appendChild(li)

      const apiCalls = document.getElementById('api-calls')
      apiCalls.appendChild(div)

      if (click) {
        document.getElementById(buttonId).click()
      }
    }
  }
}