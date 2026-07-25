# ServiceFinder

A simple website to find local service providers (plumbers, electricians, cleaners, etc.)
Built with Flask + SQLite3 + basic ML (sklearn + nltk).

## Features
- One Sign Up page (role dropdown: User or Service Provider) and one Login page
  (role dropdown: User, Service Provider, or Admin).
- User: search providers by region + service, book a service, track booking status
  (Pending / Accepted / Completed), rate & review providers after job completion.
- Service Provider (needs admin approval before login): edit profile, accept/reject
  requests, mark jobs completed, view completion history and reviews.
- Admin: manage service categories, approve/reject providers, view dashboard stats
  (total users, total providers, most popular services).
- AI Chatbot: describe your problem in plain English, it predicts the service category
  and recommends approved providers for that category, sorted by rating.
- Cost Estimator: describe the problem + pick a service, get an estimated cost range.

## Tech used
- Backend: Python, Flask
- Database: SQLite3 (raw sqlite3 module, no ORM)
- Frontend: plain HTML, CSS, JavaScript (no React/Bootstrap)
- AI/ML: nltk (text cleaning) + scikit-learn (TF-IDF + Naive Bayes / Random Forest)

## Folder Structure
```
service_finder/
├── app.py                  -> main flask app (all the routes)
├── html_helpers.py         -> builds html snippets (cards, tables, navbar) in python
├── database.py             -> sqlite3 connection helper
├── init_db.py               -> run once to create tables + default admin/services
├── download_nltk_data.py   -> run once to download nltk packages (needs internet)
├── requirements.txt
├── models/
│   ├── text_utils.py         -> nltk based text cleaning function
│   ├── train_category_model.py
│   ├── train_cost_model.py
│   ├── category_model.pkl    -> already trained, ready to use
│   ├── cost_model.pkl        -> already trained, ready to use
│   └── data/                 -> training data csv files
├── static/
│   ├── style.css
│   └── script.js
└── templates/               -> all the html pages
```

## How to run

1. Install the requirements:
   ```
   pip install -r requirements.txt
   ```

2. Create the database (this makes service_finder.db and adds a default admin + default services):
   ```
   python init_db.py
   ```

3. Run the app:
   ```
   python app.py
   ```

## Default Admin Login
- Email: admin@servicefinder.com
- Password: admin123

## Notes
- The Sign Up page has one role dropdown (User / Service Provider). Admin accounts
  aren't created through sign up - only the default admin account exists.
- New provider accounts start as "Pending" and need to be approved from the Admin -> Verify
  Providers page before they can log in.
- Region is picked from a fixed dropdown list (Kozhikode, Kochi, Thiruvananthapuram, Kannur).
  You can add more by editing the `REGIONS` list at the top of `app.py`.
- Retraining the ML models is optional - the trained `.pkl` files are already included.
  If you want to retrain: run `python download_nltk_data.py` once, then run the two
  `train_*.py` scripts inside `models/`.
