function copyToClipboard(id) {
  navigator.clipboard.writeText(document.getElementById(id).value)
}