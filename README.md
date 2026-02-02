[README.md](https://github.com/user-attachments/files/24999276/README.md)
# 🎨 RFG Palette System

**A personal color analysis engine built on 10+ years of proprietary methodology.**

The RFG Palette System is an interactive color analysis quiz that determines a client's personalized color palette through guided self-assessment and optional photo color-sampling. Built with Streamlit, it delivers instant, data-driven palette recommendations rooted in a framework developed through hands-on study with pioneering color analysts including David Kibbe, David Zyla, and John Kitchener.

---

## What It Does

The system guides clients through a series of questions about their natural coloring — skin undertone, eye pattern, hair depth and warmth, contrast level — and uses a custom matching engine to identify their optimal palette from a curated library of color families. Each palette includes coordinated colors for clothing, makeup, metallics, and neutrals.

**Two service tiers:**

| Tier | What's Included | Price |
|------|----------------|-------|
| **Essential** | Core palette quiz + digital color palette | $99 |
| **Elite** | Full quiz + expanded palette + style guidance | $179 |

---

## Project Structure

```
rfg-palette-quiz/
├── app.py            # Streamlit application — UI, quiz flow, client interaction
├── engine.py         # Palette matching engine — scoring logic, color classification
├── palettes.py       # Palette data library — curated color families and metadata
└── requirements.txt  # Python dependencies
```

---

## Tech Stack

- **Python 3**
- **Streamlit** — interactive web application framework
- **Custom color engine** — proprietary matching algorithm mapping client inputs to palette families

---

## Running Locally

```bash
# Clone the repo
git clone https://github.com/owlet-bit/rfg-palette-quiz.git
cd rfg-palette-quiz

# Install dependencies
pip install -r requirements.txt

# Launch the app
streamlit run app.py
```

---

## About the Methodology

The RFG (Rogue Fem Genius) Palette System synthesizes insights from multiple established color analysis traditions — seasonal analysis, tonal systems, Kibbe archetypes, Zyla color identities, and Kitchener essences — into an original, integrated framework. It's the product of over a decade of personal research, professional analyses, and pattern recognition across systems that are typically treated as separate disciplines.

This isn't a generic "what season are you" quiz. The engine accounts for the interplay between undertone, contrast, chroma, and value depth in ways that most consumer-facing color tools don't attempt.

---

## Status

🟢 **Active development** — deployed and serving clients.

---

## Author

Built by [owlet-bit](https://github.com/owlet-bit) — color analyst, researcher, and builder.

---

## License

This project is open source. The palette data and methodology represent original intellectual property developed over 10+ years of research and practice.
