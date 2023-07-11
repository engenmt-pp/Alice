# Alice overview

Alice is a Python/[Flask](https://flask.palletsprojects.com/en/2.3.x/) app. It has
- A Python backend/API that handles all the server-side API calls, etc.;
- A few HTML templates that Flask renders using the [Jinja2](https://palletsprojects.com/p/jinja/) template engine; and
- Some vanilla JS to manage some frontend functionality.

## An introductory example.
When a user loads goes to `go/alice/`, approximately the following happens.
- The `go` link set up through `go/go` reroutes the user to the long and cumbersome URL that points to the server where Alice runs.
- The path `/` is identified as a route assigned to the `checkout` method in `src/routes.py`.
- Partner and merchant information is loaded and passed to the `src/templates/checkout.html` Jinja2 template.
- The template is rendered into HTML and is served with the associated hand-written `src/static/styles.css` and `src/static/checkout.js` files.
- The PayPal JS SDK URL is created using the options selected on the page, and the JS SDK is loaded.
- Upon the JS SDK loading, the PayPal Smart Payment Buttons are rendered using options and methods determined using the options selected.