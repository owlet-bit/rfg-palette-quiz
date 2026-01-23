"""
RFG Palette System - Streamlit Web App
Run with: streamlit run app.py
"""

import streamlit as st
from datetime import datetime
import urllib.parse
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from engine import (
    calculate_traits, 
    determine_season, 
    trait_summary, 
    season_label, 
    detect_tensions, 
    irl_tests_for,
    trait_label
)
from palettes import palettes
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import Image
import colorsys

# Display labels for dropdown options (prettier than internal values)
DISPLAY_LABELS = {
    # Wrong metal options
    'gold_sallow': 'Gold (makes me sallow)',
    'silver_gray': 'Silver (makes me gray)',
    'no_diff': 'No difference',
    
    # Worst color options
    'dusty_rose': 'Dusty Rose',
    'icy_lavender': 'Icy Lavender',
    'icypink': 'Icy Pink',
    'hotpink': 'Hot Pink',
    
    # Best compliment options
    'dusty_rose': 'Dusty Rose',
    'cobalt': 'Cobalt Blue',
    'rust': 'Rust/Terracotta',
    'icy_lavender': 'Icy Lavender',
    'chartreuse': 'Chartreuse/Lime'
}

def format_option(option):
    """Convert internal value to pretty display label."""
    return DISPLAY_LABELS.get(option, option.replace('_', ' ').title())


def save_to_google_sheets(booking_data):
    """Save booking data to Google Sheets."""
    try:
        # Set up credentials
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
        client = gspread.authorize(creds)
        
        # Open the sheet
        sheet = client.open_by_key('1t0mh7E_oQp78Lf4ADwX_t1ctGKSxNCvhYbcij0LIPtc').sheet1
        
        # Prepare the row data
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Format HSV data as strings
        def format_hsv(color_data):
            if color_data and 'hsv' in color_data:
                h, s, v = color_data['hsv']
                return f"H{h} S{s} V{v}"
            return ""
        
        def format_hex(color_data):
            if color_data and 'hex' in color_data:
                return color_data['hex']
            return ""
        
        row = [
            timestamp,
            booking_data.get('name', ''),
            booking_data.get('email', ''),
            booking_data.get('phone', ''),
            booking_data.get('notes', ''),
            booking_data.get('season', ''),
            str(booking_data.get('confidence', '')),
            # Photo analysis results
            booking_data.get('photo_season', ''),
            booking_data.get('undertone', ''),
            booking_data.get('value', ''),
            booking_data.get('chroma', ''),
            # Iris color
            format_hex(booking_data.get('iris_color')),
            format_hsv(booking_data.get('iris_color')),
            # Hair color
            format_hex(booking_data.get('hair_color')),
            format_hsv(booking_data.get('hair_color')),
            # Skin color
            format_hex(booking_data.get('skin_color')),
            format_hsv(booking_data.get('skin_color')),
            # Favorite colors (comma-separated hex codes)
            ', '.join(booking_data.get('favorite_colors', []))
        ]
        
        # Append to sheet
        sheet.append_row(row)
        return True
    except Exception as e:
        st.error(f"Error saving to Google Sheets: {str(e)}")
        return False
    
def analyze_seasonal(iris, hair, skin):
    """
    Analyze iris, hair, and skin colors to suggest a season.
    """
    iris_h, iris_s, iris_v = iris['hsv']
    hair_h, hair_s, hair_v = hair['hsv']
    skin_h, skin_s, skin_v = skin['hsv']
    
    # UNDERTONE
    if 20 <= skin_h <= 70:
        undertone = "Warm"
        undertone_reason = f"Skin hue {skin_h}° is in warm range"
    elif skin_h >= 300 or skin_h <= 20:
        undertone = "Cool"
        undertone_reason = f"Skin hue {skin_h}° is in cool range"
    else:
        undertone = "Neutral"
        undertone_reason = f"Skin hue {skin_h}° is between warm and cool"
    
    # VALUE
    avg_value = (skin_v * 2 + hair_v + iris_v) / 4
    if avg_value >= 65:
        value = "Light"
        value_reason = f"Average value {avg_value:.0f}% is light"
    elif avg_value <= 40:
        value = "Dark"
        value_reason = f"Average value {avg_value:.0f}% is dark"
    else:
        value = "Medium"
        value_reason = f"Average value {avg_value:.0f}% is medium"
    
    # CHROMA
    avg_sat = (iris_s + hair_s) / 2
    if avg_sat >= 50:
        chroma = "Clear"
        chroma_reason = f"Average saturation {avg_sat:.0f}% is high"
    elif avg_sat <= 30:
        chroma = "Muted"
        chroma_reason = f"Average saturation {avg_sat:.0f}% is low"
    else:
        chroma = "Moderate"
        chroma_reason = f"Average saturation {avg_sat:.0f}% is moderate"
    
    # SEASON
    if undertone == "Warm":
        if value == "Light" and chroma == "Clear":
            season = "Spring"
            season_reason = "Warm + light + clear = Spring"
        elif chroma == "Muted":
            season = "Autumn"
            season_reason = "Warm + muted = Autumn family"
        else:
            season = "Spring/Autumn"
            season_reason = "Warm undertone, mixed signals"
    elif undertone == "Cool":
        if chroma == "Muted" or value == "Light":
            season = "Summer"
            season_reason = "Cool + muted or light = Summer family"
        elif chroma == "Clear" and value in ["Dark", "Medium"]:
            season = "Winter"
            season_reason = "Cool + clear + darker = Winter family"
        else:
            season = "Summer/Winter"
            season_reason = "Cool undertone, mixed signals"
    else:
        if chroma == "Muted":
            season = "Soft Summer or Soft Autumn"
            season_reason = "Neutral + muted = Soft seasons"
        else:
            season = "Needs draping"
            season_reason = "Neutral undertone - need in-person draping"
    
    return {
        'undertone': undertone, 'undertone_reason': undertone_reason,
        'value': value, 'value_reason': value_reason,
        'chroma': chroma, 'chroma_reason': chroma_reason,
        'season': season, 'season_reason': season_reason
    }

# Page config
st.set_page_config(
    page_title="RFG Palette System",
    page_icon="🎨",
    layout="centered"
)


# Custom CSS for styling
st.markdown("""
<style>
    /* Dark background */
    .stApp {
        background: linear-gradient(170deg, #2C3E50 0%, #3D4852 50%, #2D3A3A 100%);
    }
    
    .main-header {
        text-align: center;
        color: #F5F0EB;
        font-size: 2.5em;
        margin-bottom: 0.2em;
    }
    .sub-header {
        text-align: center;
        color: #D8D0C8;
        font-size: 1.2em;
        margin-bottom: 2em;
        font-style: italic;
    }
    .season-result {
        background: linear-gradient(135deg, rgba(74, 85, 104, 0.6), rgba(44, 62, 80, 0.8));
        border: 1px solid rgba(154, 143, 191, 0.3);
        color: #F5F0EB;
        padding: 2em;
        border-radius: 12px;
        text-align: center;
        margin: 2em 0;
    }
    .season-name {
        font-size: 2em;
        font-weight: bold;
        margin-bottom: 0.5em;
        color: #F5F0EB;
    }
    .confidence-badge {
        background: rgba(255,255,255,0.2);
        padding: 0.5em 1em;
        border-radius: 20px;
        display: inline-block;
    }
    .color-chip {
        display: inline-block;
        width: 30px;
        height: 30px;
        border-radius: 5px;
        margin-right: 10px;
        vertical-align: middle;
        border: 2px solid rgba(154, 143, 191, 0.3);
    }
    .progress-text {
        text-align: center;
        color: #A0A5AB;
        font-size: 0.9em;
        margin-bottom: 0.5em;
    }
    
    /* Confidence badges */
    .confidence-high {
        background: linear-gradient(135deg, #6B9B8A, #4a7c6f);
        color: white;
        padding: 0.5em 1em;
        border-radius: 20px;
        display: inline-block;
        font-weight: bold;
    }
    .confidence-medium {
        background: linear-gradient(135deg, #9A8FBF, #7a6f9f);
        color: white;
        padding: 0.5em 1em;
        border-radius: 20px;
        display: inline-block;
        font-weight: bold;
    }
    .confidence-low {
        background: linear-gradient(135deg, #C48B9F, #a46b7f);
        color: white;
        padding: 0.5em 1em;
        border-radius: 20px;
        display: inline-block;
        font-weight: bold;
    }
    
    /* Progress bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(to right, #6B9B8A, #9A8FBF);
    }
    
    /* Make help icons visible */
    [data-testid="stTooltipIcon"] svg {
        fill: #9A8FBF !important;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Header
    st.markdown('<h1 class="main-header">🎨 RFG Palette System</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Discover Your Color Season</p>', unsafe_allow_html=True)
    
    # Initialize session state
    if 'answers' not in st.session_state:
        st.session_state.answers = {}
    
    # Instructions
    with st.expander("📖 How This Works"):
        st.write("""
        This quiz analyzes your natural coloring to determine your seasonal color palette.
        Answer honestly based on your natural features (no makeup, natural lighting).
        
        The system uses weighted trait analysis to give you nuanced, accurate results.
        """)
    
    # List of all questions (for progress tracking)
    all_questions = [
        'eye_color', 'hair_color', 'skin_tone', 'jewelry', 'veins', 'eyes',
        'contrast', 'black_test', 'white_test', 'wrong_metal', 'worst_color', 'best_comp'
    ]
    
    # Initialize photo color session state
    if 'iris_color' not in st.session_state:
        st.session_state.iris_color = None
    if 'hair_color' not in st.session_state:
        st.session_state.hair_color = None
    if 'skin_color' not in st.session_state:
        st.session_state.skin_color = None
    if 'picking_mode' not in st.session_state:
        st.session_state.picking_mode = 'iris'
    if 'favorite_colors' not in st.session_state:
        st.session_state.favorite_colors = []
    
    # Calculate progress (quiz questions + photo sampling)
    quiz_answered = len([q for q in all_questions if q in st.session_state.answers])
    photo_complete = all([st.session_state.iris_color, st.session_state.hair_color, st.session_state.skin_color])
    
    # Total steps: 12 quiz questions + 1 photo step
    total_steps = len(all_questions) + 1
    completed_steps = quiz_answered + (1 if photo_complete else 0)
    progress = completed_steps / total_steps
    
    # Show progress indicator
    st.markdown(f'<p class="progress-text">Step {completed_steps} of {total_steps}</p>', unsafe_allow_html=True)
    st.progress(progress)
    st.markdown("---")
    
    # Questions section
    st.subheader("Physical Features")
    
    col1, col2 = st.columns(2)
    
    with col1:
        eye_color = st.selectbox(
            "Eye Color",
            ["blue", "green", "brown", "hazel"],
            key="eye_color_select",
            index=None,
            placeholder="Select..."
        )
        if eye_color is not None:
            st.session_state.answers['eye_color'] = eye_color
        
        hair_color = st.selectbox(
            "Natural Hair Color",
            ["blonde", "light brown", "dark brown", "black", "red"],
            key="hair_color_select",
            index=None,
            placeholder="Select..."
        )
        if hair_color is not None:
            st.session_state.answers['hair_color'] = hair_color
        
        skin_tone = st.selectbox(
            "Skin Tone",
            ["warm", "cool", "neutral"],
            key="skin_tone_select",
            index=None,
            placeholder="Select..."
        )
        if skin_tone is not None:
            st.session_state.answers['skin_tone'] = skin_tone
        
        jewelry = st.selectbox(
            "Which jewelry looks best?",
            ["gold", "silver", "both"],
            key="jewelry_select",
            index=None,
            placeholder="Select..."
        )
        if jewelry is not None:
            st.session_state.answers['jewelry'] = jewelry
        
        veins = st.selectbox(
            "Vein Color",
            ["blue", "green", "blue-green", "purple"],
            key="veins_select",
            index=None,
            placeholder="Select..."
        )
        if veins is not None:
            st.session_state.answers['veins'] = veins
        
        eyes = st.selectbox(
            "Eye Quality",
            ["bright", "soft"],
            key="eyes_select",
            index=None,
            placeholder="Select...",
            help="Bright and clear vs muted and soft"
        )
        if eyes is not None:
            st.session_state.answers['eyes'] = eyes
    
    with col2:
        contrast = st.selectbox(
            "Hair/Skin Contrast",
            ["high", "low"],
            key="contrast_select",
            index=None,
            placeholder="Select..."
        )
        if contrast is not None:
            st.session_state.answers['contrast'] = contrast
        
        black_test = st.selectbox(
            "Black near your face",
            ["yes", "softened", "no"],
            key="black_test_select",
            index=None,
            placeholder="Select...",
            help="Does pure black look good on you?"
        )
        if black_test is not None:
            st.session_state.answers['black_test'] = black_test
        
        white_test = st.selectbox(
            "Best white on you",
            ["optic", "soft", "cream"],
            key="white_test_select",
            index=None,
            placeholder="Select..."
        )
        if white_test is not None:
            st.session_state.answers['white_test'] = white_test
        
        wrong_metal = st.selectbox(
            "Wrong metal effect",
            ["gold_sallow", "silver_gray", "no_diff"],
            key="wrong_metal_select",
            index=None,
            placeholder="Select...",
            format_func=format_option,
            help="Gold makes you sallow OR silver makes you gray?"
        )
        if wrong_metal is not None:
            st.session_state.answers['wrong_metal'] = wrong_metal
        
        worst_color = st.selectbox(
            "Worst color on you",
            ["mustard", "camel", "icypink", "black", "hotpink"],
            key="worst_color_select",
            index=None,
            placeholder="Select...",
            format_func=format_option,
            help="Which color looks terrible on you?"
        )
        if worst_color is not None:
            st.session_state.answers['worst_color'] = worst_color
        
        best_comp = st.selectbox(
            "Color you get compliments in",
            ["dusty_rose", "coral", "cobalt", "rust", "icy_lavender", "chartreuse"],
            key="best_comp_select",
            index=None,
            placeholder="Select...",
            format_func=format_option
        )
        if best_comp is not None:
            st.session_state.answers['best_comp'] = best_comp
    
    # RECALCULATE progress after all selectboxes have run
    quiz_answered = len([q for q in all_questions if q in st.session_state.answers])
    photo_complete = all([st.session_state.iris_color, st.session_state.hair_color, st.session_state.skin_color])
    
    # ===== PHOTO SAMPLING SECTION (Required Step) =====
    # Show after quiz questions are complete
    if quiz_answered == len(all_questions):
        st.markdown("---")
        
        if not photo_complete:
            st.subheader("📸 Photo Color Sampling")
            st.write("**Final step!** Upload a selfie and sample your iris, hair, and skin colors.")
            st.caption("Good lighting, no makeup ideal. This helps validate your quiz results.")
            
            uploaded_file = st.file_uploader("Upload a photo", type=["jpg", "jpeg", "png"], key="selfie_upload")
            
            if uploaded_file:
                image = Image.open(uploaded_file)
                
                # Mode selector buttons
                st.write("**What are you sampling?**")
                pcol1, pcol2, pcol3 = st.columns(3)
                
                with pcol1:
                    if st.button("👁️ Iris", use_container_width=True, 
                                type="primary" if st.session_state.picking_mode == 'iris' else "secondary"):
                        st.session_state.picking_mode = 'iris'
                        st.rerun()
                with pcol2:
                    if st.button("💇 Hair", use_container_width=True,
                                type="primary" if st.session_state.picking_mode == 'hair' else "secondary"):
                        st.session_state.picking_mode = 'hair'
                        st.rerun()
                with pcol3:
                    if st.button("✋ Skin", use_container_width=True,
                                type="primary" if st.session_state.picking_mode == 'skin' else "secondary"):
                        st.session_state.picking_mode = 'skin'
                        st.rerun()
                
                st.info(f"👆 Click on the image to sample your **{st.session_state.picking_mode}** color")
                
                # Display image and get click coordinates
                coords = streamlit_image_coordinates(image, key=f"photo_{uploaded_file.name}")
                
                if coords:
                    x, y = coords["x"], coords["y"]
                    rgb = image.getpixel((x, y))
                    if len(rgb) == 4:
                        rgb = rgb[:3]
                    r, g, b = rgb
                    hex_color = f"#{r:02x}{g:02x}{b:02x}"
                    h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
                    
                    color_data = {
                        'rgb': rgb,
                        'hex': hex_color,
                        'hsv': (int(h * 360), int(s * 100), int(v * 100))
                    }
                    
                    if st.session_state.picking_mode == 'iris':
                        st.session_state.iris_color = color_data
                    elif st.session_state.picking_mode == 'hair':
                        st.session_state.hair_color = color_data
                    else:
                        st.session_state.skin_color = color_data
                
                # Display sampled colors with REDO buttons
                st.markdown("---")
                st.write("**Your Sampled Colors:**")
                scol1, scol2, scol3 = st.columns(3)
                
                with scol1:
                    st.markdown("**👁️ Iris**")
                    if st.session_state.iris_color:
                        c = st.session_state.iris_color
                        st.markdown(
                            f'<div style="background-color: {c["hex"]}; '
                            f'width: 80px; height: 80px; border-radius: 50%; '
                            f'border: 3px solid #ddd; margin: 10px 0;"></div>',
                            unsafe_allow_html=True
                        )
                        st.caption(f'{c["hex"]}')
                        if st.button("🔄 Redo", key="redo_iris"):
                            st.session_state.iris_color = None
                            st.session_state.picking_mode = 'iris'
                            st.rerun()
                    else:
                        st.markdown(
                            '<div style="background-color: #ddd; '
                            'width: 80px; height: 80px; border-radius: 50%; '
                            'border: 3px dashed #999; margin: 10px 0;"></div>',
                            unsafe_allow_html=True
                        )
                        st.caption("Not sampled yet")
                
                with scol2:
                    st.markdown("**💇 Hair**")
                    if st.session_state.hair_color:
                        c = st.session_state.hair_color
                        st.markdown(
                            f'<div style="background-color: {c["hex"]}; '
                            f'width: 80px; height: 80px; border-radius: 50%; '
                            f'border: 3px solid #ddd; margin: 10px 0;"></div>',
                            unsafe_allow_html=True
                        )
                        st.caption(f'{c["hex"]}')
                        if st.button("🔄 Redo", key="redo_hair"):
                            st.session_state.hair_color = None
                            st.session_state.picking_mode = 'hair'
                            st.rerun()
                    else:
                        st.markdown(
                            '<div style="background-color: #ddd; '
                            'width: 80px; height: 80px; border-radius: 50%; '
                            'border: 3px dashed #999; margin: 10px 0;"></div>',
                            unsafe_allow_html=True
                        )
                        st.caption("Not sampled yet")
                
                with scol3:
                    st.markdown("**✋ Skin**")
                    if st.session_state.skin_color:
                        c = st.session_state.skin_color
                        st.markdown(
                            f'<div style="background-color: {c["hex"]}; '
                            f'width: 80px; height: 80px; border-radius: 50%; '
                            f'border: 3px solid #ddd; margin: 10px 0;"></div>',
                            unsafe_allow_html=True
                        )
                        st.caption(f'{c["hex"]}')
                        if st.button("🔄 Redo", key="redo_skin"):
                            st.session_state.skin_color = None
                            st.session_state.picking_mode = 'skin'
                            st.rerun()
                    else:
                        st.markdown(
                            '<div style="background-color: #ddd; '
                            'width: 80px; height: 80px; border-radius: 50%; '
                            'border: 3px dashed #999; margin: 10px 0;"></div>',
                            unsafe_allow_html=True
                        )
                        st.caption("Not sampled yet")
                
                # Check if all colors are now sampled
                photo_complete = all([st.session_state.iris_color, st.session_state.hair_color, st.session_state.skin_color])
                
                if photo_complete:
                    st.success("✅ All colors sampled! Scroll down for your results.")
        
        # Show results only when BOTH quiz AND photo are complete
        if photo_complete:
            st.markdown("---")
            st.success("✨ Quiz complete! Here are your results:")
            
            # Calculate from quiz
            traits = calculate_traits(st.session_state.answers)
            result = determine_season(traits)
            
            # Also run photo analysis
            photo_result = analyze_seasonal(
                st.session_state.iris_color,
                st.session_state.hair_color,
                st.session_state.skin_color
            )
            
            # Display results (pass photo_result too)
            display_results(traits, result, photo_result)


def display_results(traits, result, photo_result=None):
    """Display the season results in a beautiful format."""
    season = result['season']
    confidence_percent = result['confidence_percent']
    confidence_label = result['confidence_label']
    winner_score = result['winner_score']
    runner = result['runner_up']
    runner_score = result['runner_score']
    ranked = result['ranked']
    
    # Main result card - with dynamic confidence coloring
    if confidence_percent > 75:
        badge_class = "confidence-high"
    elif confidence_percent > 45:
        badge_class = "confidence-medium"
    else:
        badge_class = "confidence-low"

    st.markdown(f"""
    <div class="season-result">
        <div class="season-name">{season_label(season)}</div>
        <div class="{badge_class}">{confidence_percent}% Match · {confidence_label}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Photo analysis comparison (if available)
    if photo_result:
        st.subheader("📸 Photo Analysis")
        pcol1, pcol2 = st.columns(2)
        
        with pcol1:
            st.markdown("**Your Coloring (from photo):**")
            st.write(f"• Undertone: {photo_result['undertone']}")
            st.write(f"• Value: {photo_result['value']}")
            st.write(f"• Chroma: {photo_result['chroma']}")
        
        with pcol2:
            st.markdown("**Photo suggests:**")
            st.write(f"🎨 **{photo_result['season']}**")
            st.caption(photo_result['season_reason'])
        
        # Compare quiz vs photo results
        if photo_result['season'].lower() != season.lower() and photo_result['season'] not in ["Needs draping", "Could be any season"]:
            if "/" in photo_result['season']:
                # Photo result is ambiguous
                st.info(f"📊 Quiz says **{season_label(season)}**, photo analysis is between seasons. This is common - in-person draping gives the final answer!")
            else:
                st.warning(f"📊 Quiz says **{season_label(season)}**, photo suggests **{photo_result['season']}**. This tension is useful data for your consultation!")
        else:
            st.success("✅ Quiz and photo analysis are aligned!")
        
        # Show HSV raw data
        with st.expander("🔬 Raw HSV Data"):
            for name, key in [("Iris", "iris_color"), ("Hair", "hair_color"), ("Skin", "skin_color")]:
                color = st.session_state.get(key)
                if color:
                    h, s, v = color['hsv']
                    st.caption(f"{name}: {color['hex']} → H={h}° S={s}% V={v}%")
    
    # Trait Profile
    st.subheader("📊 Your Trait Profile")
    dominant, weak = trait_summary(traits, top_n=4, weak_n=2)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Dominant Traits**")
        if dominant:
            for k, v in dominant:
                st.write(f"✨ {trait_label(k)}: {v} points")
        else:
            st.write("None detected")
    
    with col2:
        st.markdown("**Weaker Traits**")
        if weak:
            for k, v in weak:
                st.write(f"🔹 {trait_label(k)}: {v} points")
        else:
            st.write("N/A")
    
    if dominant:
        st.info(f"💡 **Key Insight:** {trait_label(dominant[0][0])} is your strongest driver.")
    
    # Mixed result analysis
    tight_gap = (winner_score - runner_score) <= 6
    not_clear = confidence_percent < 75
    
    if tight_gap or not_clear:
        st.subheader("🔄 Mixed Result Analysis")
        st.warning(f"You're landing between **{season_label(season)}** and **{season_label(runner)}**.")
        st.write(f"*Top contenders separated by {winner_score - runner_score} points*")
        
        tensions = detect_tensions(traits)
        if tensions:
            st.markdown("**Why this is mixed:**")
            for t in tensions[:2]:
                st.write(f"• {t}")
        
        tests = irl_tests_for(season, runner, traits)
        if tests:
            st.markdown("**To confirm (pick 1-2 tests):**")
            for test in tests:
                st.write(f"• {test}")
    
    # Top contenders
    st.subheader("🏆 Top Contenders")
    for s, sc in ranked[:3]:
        st.write(f"**{season_label(s)}:** {sc} points")
    
    # Color palette
    st.subheader("🎨 Your Recommended Colors")
    
    if season in palettes:
        user_palette = palettes[season]
        
        # Create color grid
        colors = list(user_palette.items())
        
        # Display in rows of 5
        for i in range(0, len(colors), 5):
            cols = st.columns(5)
            for j, col in enumerate(cols):
                if i + j < len(colors):
                    color_name, hex_code = colors[i + j]
                    with col:
                        st.markdown(
                            f'<div style="background-color: {hex_code}; '
                            f'height: 60px; border-radius: 8px; margin-bottom: 5px; '
                            f'border: 2px solid #ddd;"></div>',
                            unsafe_allow_html=True
                        )
                        st.caption(f"**{color_name.title()}**")
                        st.caption(f"`{hex_code}`")
        
        # Downloadable palette
        st.markdown("---")
        palette_text = "\n".join([f"{name.title()}: {hex_code}" for name, hex_code in user_palette.items()])
        st.download_button(
            label="💾 Download Your Palette",
            data=palette_text,
            file_name=f"{season}_palette.txt",
            mime="text/plain"
        )
    
    # ===== COLORS YOU'RE DRAWN TO (Optional) =====
    st.markdown("---")
    st.subheader("🎨 Colors You're Drawn To (Optional)")
    st.write("Upload any image with colors you love - a painting, outfit, nature photo, whatever calls to you.")
    
    fav_file = st.file_uploader("Upload an inspiration image", type=["jpg", "jpeg", "png"], key="fav_upload")
    
    if fav_file:
        fav_image = Image.open(fav_file)
        
        st.write("👆 Click on colors you're drawn to (pick as many as you want)")
        
        fav_coords = streamlit_image_coordinates(fav_image, key=f"fav_{fav_file.name}")
        
        if fav_coords:
            x = fav_coords["x"]
            y = fav_coords["y"]
            
            rgb = fav_image.getpixel((x, y))
            if len(rgb) == 4:
                rgb = rgb[:3]
            
            r, g, b = rgb
            hex_color = f"#{r:02x}{g:02x}{b:02x}"
            
            # Avoid duplicates
            if hex_color not in st.session_state.favorite_colors:
                st.session_state.favorite_colors.append(hex_color)
        
        # Display picked colors
        if st.session_state.favorite_colors:
            st.write("**Your picked colors:**")
            
            # Display as swatches in a row
            cols = st.columns(min(len(st.session_state.favorite_colors), 8))
            for i, color in enumerate(st.session_state.favorite_colors[:8]):
                with cols[i]:
                    st.markdown(
                        f'<div style="background-color: {color}; '
                        f'width: 50px; height: 50px; border-radius: 8px; '
                        f'border: 2px solid #ddd;"></div>',
                        unsafe_allow_html=True
                    )
                    st.caption(color)
            
            # Show overflow if more than 8
            if len(st.session_state.favorite_colors) > 8:
                st.caption(f"...and {len(st.session_state.favorite_colors) - 8} more")
            
            if st.button("🗑️ Clear favorites"):
                st.session_state.favorite_colors = []
                st.rerun()

    # CTA
    st.markdown("---")
    st.subheader("✨ Next Steps")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Booking form
        with st.form("booking_form", clear_on_submit=True):
            st.markdown("**📅 Book Your Consultation**")
            
            name = st.text_input("Full Name*", placeholder="Jane Doe")
            email = st.text_input("Email*", placeholder="jane@example.com")
            phone = st.text_input("Phone", placeholder="(555) 123-4567")
            notes = st.text_area(
                "Anything we should know?", 
                placeholder="Questions, concerns, or goals for your consultation",
                height=100
            )
            
            submitted = st.form_submit_button("Continue to Booking →", use_container_width=True)
            
            if submitted:
                # Validation
                if not name or not email:
                    st.error("⚠️ Please fill in your name and email")
                elif "@" not in email:
                    st.error("⚠️ Please enter a valid email")
                else:
                    # Get photo analysis result for storage
                    photo_analysis = analyze_seasonal(
                        st.session_state.iris_color,
                        st.session_state.hair_color,
                        st.session_state.skin_color
                    )
                    
                    # Store in session state with ALL data
                    st.session_state.booking_info = {
                        'name': name,
                        'email': email,
                        'phone': phone,
                        'notes': notes,
                        'season': season,
                        'confidence': confidence_percent,
                        # Photo analysis results
                        'photo_season': photo_analysis['season'],
                        'undertone': photo_analysis['undertone'],
                        'value': photo_analysis['value'],
                        'chroma': photo_analysis['chroma'],
                        # Raw color data
                        'iris_color': st.session_state.iris_color,
                        'hair_color': st.session_state.hair_color,
                        'skin_color': st.session_state.skin_color,
                        # Optional favorite colors
                        'favorite_colors': st.session_state.favorite_colors
                    }
                    
                    # Save to Google Sheets
                    with st.spinner("Saving your information..."):
                        success = save_to_google_sheets(st.session_state.booking_info)
                    
                    if success:
                        st.success(f"✅ Thanks {name}! Your information has been saved.")
                        
                        # Build Calendly URL with pre-filled info
                        calendly_base = "https://calendly.com/owlet358/60min"
                        params = {
                            'name': name,
                            'email': email
                        }
                        if phone:
                            params['a1'] = phone  # Custom field for phone
                        
                        calendly_url = f"{calendly_base}?{urllib.parse.urlencode(params)}"
                        
                        # Show booking link
                        st.info("📅 Click below to schedule your consultation!")
                        st.link_button("Schedule Your Consultation →", calendly_url, use_container_width=True)
                        
                        # Auto-redirect after 3 seconds
                        st.markdown(f"""
                        <meta http-equiv="refresh" content="3;url={calendly_url}">
                        <p style="text-align: center; color: #666; font-size: 0.9em;">
                        Redirecting to booking page in 3 seconds...
                        </p>
                        """, unsafe_allow_html=True)
                    else:
                        st.warning("⚠️ There was an issue saving your data, but we've recorded your interest!")
    
    with col2:
        if st.button("🔄 Retake Quiz", use_container_width=True):
            st.session_state.answers = {}
            st.session_state.iris_color = None
            st.session_state.hair_color = None
            st.session_state.skin_color = None
            st.session_state.picking_mode = 'iris'
            st.session_state.favorite_colors = []
            st.rerun()


if __name__ == "__main__":
    main()
