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
