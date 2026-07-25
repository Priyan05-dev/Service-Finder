# Builds html snippets (cards, tables, navbar) in python so templates stay simple

from flask import session, get_flashed_messages


def build_navbar():
    role = session.get("role")
    name = session.get("name")

    if role == "user":
        return '''
        <a href="/user/dashboard">Dashboard</a>
        <a href="/search">Find a Service</a>
        <a href="/my_bookings">My Bookings</a>
        <a href="/chatbot">Chatbot</a>
        <a href="/cost_estimator">Cost Estimator</a>
        <a href="/logout">Logout (''' + str(name) + ''')</a>
        '''
    elif role == "provider":
        return '''
        <a href="/provider/dashboard">Dashboard</a>
        <a href="/provider/profile">My Profile</a>
        <a href="/provider/requests">Requests</a>
        <a href="/provider/history">History</a>
        <a href="/logout">Logout (''' + str(name) + ''')</a>
        '''
    elif role == "admin":
        return '''
        <a href="/admin/dashboard">Dashboard</a>
        <a href="/admin/services">Manage Services</a>
        <a href="/admin/verify">Verify Providers</a>
        <a href="/logout">Logout</a>
        '''
    else:
        return '''
        <a href="/login">Login</a>
        <a href="/signup">Sign Up</a>
        '''


def build_flash():
    messages = get_flashed_messages()
    html = ""
    for msg in messages:
        html += '<div class="flash">' + msg + '</div>\n'
    return html


def build_index_section():
    role = session.get("role")
    name = session.get("name")
    if role:
        return '<p>You are logged in as <b>' + str(name) + '</b> (' + str(role) + ').</p>'
    return '''
    <div class="home-links">
        <a href="/signup">Sign Up</a>
        <a href="/login">Login</a>
    </div>
    '''


def build_service_options(services, selected=None):
    html = ""
    for s in services:
        name = s["name"]
        chosen = " selected" if name == selected else ""
        html += '<option value="' + name + '"' + chosen + '>' + name + '</option>\n'
    return html


def build_region_options(regions, selected=None):
    html = ""
    for r in regions:
        chosen = " selected" if r == selected else ""
        html += '<option value="' + r + '"' + chosen + '>' + r + '</option>\n'
    return html


def build_provider_cards(providers):
    if len(providers) == 0:
        return "<p>No providers found matching your search. Try a different region or service.</p>"

    html = ""
    for p in providers:
        if p.get("avg_rating"):
            rating_line = "<p>Rating: " + str(p["avg_rating"]) + " / 5 (" + str(p["total_reviews"]) + " reviews)</p>"
        else:
            rating_line = '<p class="small-text">No reviews yet</p>'

        html += '''
        <div class="card">
            <h3>''' + p["name"] + ''' <span class="small-text">(''' + p.get("service_category", "") + ''')</span></h3>
            <p>Region: ''' + p["region"] + ''' &nbsp;|&nbsp; Experience: ''' + str(p["experience"]) + ''' years</p>
            ''' + rating_line + '''
            <p>''' + (p["bio"] or "") + '''</p>
            <a class="btn" href="/provider/''' + str(p["id"]) + '''">View Details</a>
        </div>
        '''
    return html


def build_reviews_html(reviews):
    if len(reviews) == 0:
        return '<p class="small-text">No reviews yet.</p>'

    html = ""
    for r in reviews:
        html += '''
        <div class="card">
            <b>''' + r["user_name"] + '''</b> rated ''' + str(r["rating"]) + '''/5
            <p>''' + (r["comment"] or "") + '''</p>
        </div>
        '''
    return html


def build_my_bookings_html(bookings, reviewed_ids):
    if len(bookings) == 0:
        return '<p>You haven\'t requested any services yet. <a href="/search">Find one now</a>.</p>'

    html = ""
    for b in bookings:
        action_html = ""
        if b["status"] == "Completed":
            if b["id"] in reviewed_ids:
                action_html = '<p class="small-text">You already reviewed this job.</p>'
            else:
                action_html = '<a class="btn" href="/review/' + str(b["id"]) + '">Rate & Review</a>'

        html += '''
        <div class="card">
            <h3>''' + b["service_name"] + ''' - ''' + b["provider_name"] + '''</h3>
            <p>Date/Time: ''' + b["booking_date"] + ''' at ''' + b["booking_time"] + '''</p>
            <p>Details: ''' + (b["description"] or "") + '''</p>
            <p>Status: <span class="status-''' + b["status"] + '''">''' + b["status"] + '''</span></p>
            ''' + action_html + '''
        </div>
        '''
    return html


def build_provider_requests_html(bookings):
    if len(bookings) == 0:
        return "<p>No service requests yet.</p>"

    html = ""
    for b in bookings:
        action_html = ""
        if b["status"] == "Pending":
            action_html = '''
            <form method="POST" action="/provider/requests/''' + str(b["id"]) + '''/accept" style="display:inline;">
                <button type="submit" >Accept</button>
            </form>
            <form method="POST" action="/provider/requests/''' + str(b["id"]) + '''/reject" style="display:inline;">
                <button type="submit" >Reject</button>
            </form>
            '''
        elif b["status"] == "Accepted":
            action_html = '''
            <form method="POST" action="/provider/requests/''' + str(b["id"]) + '''/complete">
                <button type="submit" >Mark as Completed</button>
            </form>
            '''

        html += '''
        <div class="card">
            <h3>''' + b["service_name"] + ''' - ''' + b["user_name"] + '''</h3>
            <p>Contact: ''' + (b["user_phone"] or "") + '''</p>
            <p>Date/Time: ''' + b["booking_date"] + ''' at ''' + b["booking_time"] + '''</p>
            <p>Details: ''' + (b["description"] or "") + '''</p>
            <p>Status: <span class="status-''' + b["status"] + '''">''' + b["status"] + '''</span></p>
            ''' + action_html + '''
        </div>
        '''
    return html


def build_popular_services_table(popular_services):
    if len(popular_services) == 0:
        return '<p class="small-text">No bookings yet.</p>'

    html = '<table><tr><th>Service</th><th>Total Bookings</th></tr>\n'
    for s in popular_services:
        html += "<tr><td>" + s["service_name"] + "</td><td>" + str(s["total"]) + "</td></tr>\n"
    html += "</table>"
    return html


def build_pending_msg(pending_providers):
    if pending_providers > 0:
        return ('<p class="small-text">' + str(pending_providers) +
                ' provider(s) waiting for approval. <a href="/admin/verify">Review now</a></p>')
    return ""


def build_admin_services_table(services):
    html = '<table><tr><th>Service Name</th><th>Action</th></tr>\n'
    for s in services:
        html += '''
        <tr>
            <td>''' + s["name"] + '''</td>
            <td>
                <form method="POST" action="/admin/services/delete/''' + str(s["id"]) + '''"
                      onsubmit="return confirmAction('Remove this service?')" style="margin:0;">
                    <button type="submit" style="margin-top:0;">Remove</button>
                </form>
            </td>
        </tr>
        '''
    html += "</table>"
    return html


def build_pending_providers_html(providers):
    if len(providers) == 0:
        return "<p>No pending provider applications.</p>"

    html = ""
    for p in providers:
        html += '''
        <div class="card">
            <h3>''' + p["name"] + '''</h3>
            <p>Email: ''' + p["email"] + ''' | Phone: ''' + (p["phone"] or "") + '''</p>
            <p>Service: ''' + p["service_category"] + ''' | Region: ''' + p["region"] + ''' | Experience: ''' + str(p["experience"]) + ''' years</p>
            <p>Bio: ''' + (p["bio"] or "") + '''</p>
            <form method="POST" action="/admin/verify/''' + str(p["id"]) + '''/approve" style="display:inline;">
                <button type="submit" >Approve</button>
            </form>
            <form method="POST" action="/admin/verify/''' + str(p["id"]) + '''/reject" style="display:inline;">
                <button type="submit" >Reject</button>
            </form>
        </div>
        '''
    return html


def build_chatbot_result_html(predicted_category, recommended_providers):
    if predicted_category is None:
        return ""

    html = '''
    <div class="result-box">
        <p>Based on what you described, this looks like a <b>''' + predicted_category + '''</b> issue.</p>
    </div>
    <h3 style="margin-top:20px;">Recommended Providers</h3>
    '''

    if len(recommended_providers) == 0:
        html += "<p>No approved providers found for this service category yet.</p>"
    else:
        for p in recommended_providers:
            html += '''
            <div class="card">
                <h3>''' + p["name"] + '''</h3>
                <p>Region: ''' + p["region"] + ''' | Experience: ''' + str(p["experience"]) + ''' years</p>
                <p>Rating: ''' + str(p["avg_rating"]) + ''' / 5 (''' + str(p["total_reviews"]) + ''' reviews)</p>
                <p>''' + (p["bio"] or "") + '''</p>
                <a class="btn" href="/provider/''' + str(p["id"]) + '''">View Details</a>
            </div>
            '''
    return html


def build_cost_result_html(estimated_cost, cost_low, cost_high):
    if estimated_cost is None:
        return ""
    return '''
    <div class="result-box">
        <h3>Estimated Cost: Rs. ''' + str(cost_low) + ''' - Rs. ''' + str(cost_high) + '''</h3>
        <p class="small-text">This is only an approximate estimate based on similar past jobs.
            The actual cost may vary depending on the provider and the exact nature of the problem.</p>
    </div>
    '''
