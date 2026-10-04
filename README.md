# PocketSmart AI

GenAI-powered, budget-based recommendation system for Interior Design, Party/Event planning and Jewelry matching, built with Streamlit and Google Gemini.

## Run
```
pip install -r requirements.txt
export GEMINI_API_KEY=your_key      # Windows: set GEMINI_API_KEY=your_key
streamlit run app.py
```
Get a free key at https://aistudio.google.com. Without a key the app runs in demo mode with rule-based plans.

## Change the model
Set `GEMINI_MODEL` (e.g. a Flash model for speed, a Pro model for deeper planning) or edit it in the sidebar.

## How it works
1. Adaptive form captures budget and context (fields change with your answers).
2. Prompt + budget rules sent to Gemini, which returns JSON (allocations, items, tips).
3. UI shows allocation chart, item table with platform search links, and a live budget tracker.
4. Prices are AI estimates; links are platform search pages, so nothing is invented.

## Files
- app.py: the whole app
- requirements.txt
