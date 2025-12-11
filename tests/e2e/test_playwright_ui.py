import time
from uuid import uuid4
import pytest


@pytest.mark.e2e
def test_ui_bread_operations(page, fastapi_server: str):
    """End-to-end UI test covering register, login, create/read/update/delete calculations.

    Uses the browser `page` fixture from `conftest.py` and the running FastAPI `base_url`.
    """
    # Create a unique user
    username = f"ui_user_{uuid4().hex[:8]}"
    email = f"{username}@example.com"
    password = "SecurePass123!"
    first_name = "UI"
    last_name = "Tester"

    # 1. Register via UI
    base_url = fastapi_server.rstrip('/')
    page.goto(f"{base_url}/register")
    page.fill("#username", username)
    page.fill("#email", email)
    page.fill("#first_name", first_name)
    page.fill("#last_name", last_name)
    page.fill("#password", password)
    page.fill("#confirm_password", password)
    page.click("button[type='submit']")

    # Registration redirects to login after a short delay; wait for login page
    page.wait_for_url("**/login", timeout=10000)

    # 2. Login via UI
    page.fill("#username", username)
    page.fill("#password", password)
    page.click("button[type='submit']")
    page.wait_for_url("**/dashboard", timeout=10000)

    # 3. Create a new calculation (addition)
    page.fill('#calcInputs', '10, 3, 2')
    page.select_option('#calcType', 'addition')
    page.click("#calculationForm button[type='submit']")

    # Wait for the success message or table row to appear
    page.wait_for_selector('#successAlert, #calculationsTable td', timeout=10000)

    # Verify a table cell contains the expected result 15.5
    assert page.locator("#calculationsTable td", has_text="15.5").count() > 0

    # 4. Click the View link for the first calculation row
    # We search for the 'View' link associated with the created result
    view_links = page.locator("a:has-text('View')")
    assert view_links.count() > 0
    view_links.first.click()
    page.wait_for_url("**/dashboard/view/**", timeout=10000)
    # Extract calculation ID from url
    view_url = page.url
    calc_id = view_url.rstrip('/').split('/')[-1]

    # Confirm details view contains the result and the inputs
    assert page.locator('#calcDetails', has_text='15.5').count() > 0
    assert page.locator('#calcDetails', has_text='10, 3, 2').count() > 0

    # 5. Edit the calculation
    # Click Edit and wait for edit page
    page.locator('#editLink').click()
    page.wait_for_url("**/dashboard/edit/**", timeout=10000)

    # Change inputs to 5, 6 and save (addition result is 11)
    page.fill('#calcInputs', '5, 6')
    page.click('#editCalculationForm button[type="submit"]')

    # Wait for redirect back to details and updated value
    page.wait_for_url("**/dashboard/view/**", timeout=10000)
    # Wait for the new result to be visible
    assert page.locator('#calcDetails', has_text='11').count() > 0

    # 6. Delete the calculation
    # Accept the confirm dialog
    page.on('dialog', lambda dialog: dialog.accept())
    page.click('#deleteBtn')
    # After deletion, the app redirects back to dashboard
    page.wait_for_url('**/dashboard', timeout=10000)

    # Verify the deleted calculation is gone by attempting to retrieve it via API
    res_after_delete = page.evaluate(
        "async (baseUrl, calcId) => { const r = await fetch(baseUrl + '/calculations/' + calcId); return { status: r.status, text: await r.text() }; }",
        base_url,
        calc_id
    )
    assert res_after_delete['status'] == 404


@pytest.mark.e2e
def test_ui_invalid_input_and_unauthorized_access(page, fastapi_server: str):
    """Negative path tests: invalid inputs and unauthorized access handling through UI.
    """
    # Create a unique user and login using the UI like before
    username = f"ui_user_{uuid4().hex[:8]}"
    email = f"{username}@example.com"
    password = "SecurePass123!"

    base_url = fastapi_server.rstrip('/')
    page.goto(f"{base_url}/register")
    page.fill('#username', username)
    page.fill('#email', email)
    page.fill('#first_name', 'Neg')
    page.fill('#last_name', 'Tester')
    page.fill('#password', password)
    page.fill('#confirm_password', password)
    page.click("button[type='submit']")
    page.wait_for_url('**/login', timeout=10000)
    page.fill('#username', username)
    page.fill('#password', password)
    page.click("button[type='submit']")
    page.wait_for_url('**/dashboard', timeout=10000)

    # Negative case: Try creating calculation with only one input
    page.fill('#calcInputs', '100')
    page.select_option('#calcType', 'addition')
    page.click('#calculationForm button[type="submit"]')

    # The UI should show an error alert
    page.wait_for_selector('#errorAlert', timeout=5000)
    assert page.locator('#errorMessage', has_text='at least two').count() > 0

    # Negative case: Division by zero on creation (client-side validation)
    page.fill('#calcInputs', '10, 0')
    page.select_option('#calcType', 'division')
    page.click('#calculationForm button[type="submit"]')
    page.wait_for_selector('#errorAlert', timeout=5000)
    assert page.locator('#errorMessage', has_text='Division by zero').count() > 0

    # Negative case: Clear tokens and navigate to dashboard, should redirect to login
    page.evaluate("localStorage.clear()")
    page.goto(f"{base_url}/dashboard")
    page.wait_for_url('**/login', timeout=5000)

    # Negative case: Attempt an API call without token (via browser fetch)
    res = page.evaluate("async (baseUrl) => { const r = await fetch(baseUrl + '/calculations'); return { status: r.status, text: await r.text() }; }", base_url)
    assert res['status'] == 401, f"Expected 401 for unauthenticated fetch, got {res['status']}\nBody: {res['text']}"

    # Negative case: Invalid operation type should return 400 when called via API
    invalid_post = page.evaluate(
        "async (baseUrl) => { const r = await fetch(baseUrl + '/calculations', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ type: 'invalid', inputs: [1,2] }) }); return { status: r.status, text: await r.text() }; }",
        base_url
    )
    assert invalid_post['status'] == 400, f"Expected 400 for invalid calc type, got {invalid_post['status']}\nBody: {invalid_post['text']}"
