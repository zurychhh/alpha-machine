# 🎨 BRAND GUIDELINES & VISUAL IDENTITY SYSTEM
## Rafał Oleksiak Consulting

**Version:** 1.0  
**Last Updated:** January 4, 2026  
**Created By:** Claude (Anthropic) + Rafał Oleksiak  
**Purpose:** Complete visual identity system for consistent implementation across all digital properties

---

## 📋 TABLE OF CONTENTS

1. [Brand Essence](#brand-essence)
2. [Color System](#color-system)
3. [Typography](#typography)
4. [Logo & Brand Mark](#logo--brand-mark)
5. [Visual Style](#visual-style)
6. [UI Components](#ui-components)
7. [Motion & Animation](#motion--animation)
8. [Imagery & Photography](#imagery--photography)
9. [Content Voice & Tone](#content-voice--tone)
10. [Implementation Examples](#implementation-examples)
11. [Do's and Don'ts](#dos-and-donts)

---

## 🎯 BRAND ESSENCE

### Brand Personality: **Tech-Forward Innovator**

A premium consulting brand that combines:
- **Technical sophistication** with human approachability
- **Data-driven precision** with creative problem-solving  
- **Enterprise credibility** with startup agility
- **ROI-focused methodology** with personalized service

### Key Attributes:
- 🔮 **Futuristic** - Sci-fi aesthetic, CRT effects, retro-tech vibes
- 💎 **Premium** - Glass morphism, depth, sophisticated gradients
- ⚡ **Dynamic** - Animated elements, interactive experiences
- 📊 **Data-Driven** - Metrics-focused, measurable outcomes
- 🎯 **ROI-Obsessed** - "Zawsze syntezuj" methodology

### Brand Positioning:
"I don't just analyze — I synthesize. I turn CRM systems into revenue engines with measurable ROI in 30 days."

---

## 🎨 COLOR SYSTEM

### Primary Colors

#### Moonlit Grey (Primary Background)
```css
--color-moonlit-grey: #1a1a2e;
--color-moonlit-grey-rgb: 26, 26, 46;
```
**Usage:** Main backgrounds, hero sections, premium cards  
**Psychology:** Sophistication, mystery, premium quality  
**Contrast Ratio:** Passes WCAG AA with white text (13.8:1)

#### Vivid Purple (Primary Accent)
```css
--color-vivid-purple: #9333ea;
--color-vivid-purple-rgb: 147, 51, 234;
```
**Usage:** CTAs, interactive elements, highlights  
**Psychology:** Innovation, creativity, premium tech  
**Contrast Ratio:** Passes WCAG AA with white text (5.2:1)

---

### Secondary Colors

#### Electric Blue (Secondary Accent)
```css
--color-electric-blue: #3b82f6;
--color-electric-blue-rgb: 59, 130, 246;
```
**Usage:** Secondary CTAs, info highlights, icons  
**Accessibility:** WCAG AA compliant on dark backgrounds

#### Cosmic Teal (Tertiary Accent)
```css
--color-cosmic-teal: #14b8a6;
--color-cosmic-teal-rgb: 20, 184, 166;
```
**Usage:** Success states, positive metrics, growth indicators

---

### Neutral Grays

#### Surface Colors
```css
--color-surface-dark: #16213e;      /* Dark surface */
--color-surface-medium: #0f3460;    /* Medium surface */
--color-surface-light: #533483;     /* Light surface (purple tint) */
```

#### Text Colors
```css
--color-text-primary: #ffffff;      /* Primary text */
--color-text-secondary: #a0aec0;    /* Secondary text (70% opacity) */
--color-text-tertiary: #718096;     /* Tertiary text (50% opacity) */
--color-text-disabled: #4a5568;     /* Disabled text (30% opacity) */
```

---

### Gradient System

#### Purple Gradient (Hero, Premium CTAs)
```css
background: linear-gradient(135deg, #9333ea 0%, #6b21a8 100%);
```
**Usage:** Hero CTAs, premium buttons, highlights

#### Blue-Purple Gradient (Secondary)
```css
background: linear-gradient(135deg, #3b82f6 0%, #9333ea 100%);
```
**Usage:** Secondary CTAs, cards, feature highlights

#### Dark Gradient (Backgrounds)
```css
background: linear-gradient(180deg, #1a1a2e 0%, #0f1419 100%);
```
**Usage:** Section backgrounds, overlays

#### Glass Morphism Gradient
```css
background: linear-gradient(135deg, 
  rgba(147, 51, 234, 0.1) 0%, 
  rgba(59, 130, 246, 0.05) 100%);
backdrop-filter: blur(20px);
border: 1px solid rgba(255, 255, 255, 0.1);
```
**Usage:** Premium cards, methodology cards, floating elements

---

## 📝 TYPOGRAPHY

### Font Families

#### Poppins (Primary - Headings)
```css
font-family: 'Poppins', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
```
**Weights Used:** 400 (Regular), 600 (SemiBold), 700 (Bold), 900 (Black)  
**Character Set:** Latin only (optimized subset)  
**Hosting:** Local `/app/fonts/Poppins/` (not Google Fonts)  
**Usage:** Headlines (H1-H3), CTAs, Navigation, Logo

**Why Poppins:**
- Geometric sans-serif = modern, tech-forward
- Excellent readability at all sizes
- Strong personality without being distracting
- Works well for data-heavy content

#### DM Sans (Secondary - Body)
```css
font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
```
**Weights Used:** 400 (Regular), 500 (Medium), 700 (Bold)  
**Character Set:** Latin only (optimized subset)  
**Hosting:** Local `/app/fonts/DMSans/`  
**Usage:** Body copy, paragraphs, lists, form labels

**Why DM Sans:**
- Optimized for digital reading
- Lower x-height than Poppins (visual hierarchy)
- Neutral, professional
- Excellent for long-form content

---

### Type Scale (Desktop)

```css
/* Headings */
--font-size-h1: 60px;      /* Hero headlines */
--font-size-h2: 48px;      /* Section headlines */
--font-size-h3: 36px;      /* Subsection headlines */
--font-size-h4: 28px;      /* Card headlines */
--font-size-h5: 24px;      /* Small headlines */
--font-size-h6: 20px;      /* Overlines */

/* Body */
--font-size-body-large: 20px;    /* Hero subheadlines */
--font-size-body: 18px;          /* Regular body */
--font-size-body-small: 16px;    /* Secondary body */
--font-size-caption: 14px;       /* Captions, labels */
--font-size-overline: 12px;      /* Overlines, tags */

/* Weights */
--font-weight-regular: 400;
--font-weight-medium: 500;
--font-weight-semibold: 600;
--font-weight-bold: 700;
--font-weight-black: 900;
```

---

### Type Scale (Mobile)

```css
/* Headings (Mobile) */
--font-size-h1-mobile: 32px;   /* Hero headlines */
--font-size-h2-mobile: 28px;   /* Section headlines */
--font-size-h3-mobile: 24px;   /* Subsection headlines */
--font-size-h4-mobile: 20px;   /* Card headlines */
--font-size-h5-mobile: 18px;   /* Small headlines */
--font-size-h6-mobile: 16px;   /* Overlines */

/* Body (Mobile) */
--font-size-body-large-mobile: 18px;
--font-size-body-mobile: 16px;
--font-size-body-small-mobile: 14px;
--font-size-caption-mobile: 13px;
--font-size-overline-mobile: 11px;
```

---

### Typography Examples

```css
/* H1 - Hero Headline */
.hero-headline {
  font-family: 'Poppins', sans-serif;
  font-size: 60px;
  font-weight: 700;
  line-height: 1.1;
  letter-spacing: -0.02em;
  color: #ffffff;
}

/* H2 - Section Headline */
.section-headline {
  font-family: 'Poppins', sans-serif;
  font-size: 48px;
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: -0.01em;
  color: #ffffff;
}

/* Body - Regular */
.body-text {
  font-family: 'DM Sans', sans-serif;
  font-size: 18px;
  font-weight: 400;
  line-height: 1.7;
  letter-spacing: 0;
  color: rgba(255, 255, 255, 0.7);
}

/* CTA Button */
.cta-button {
  font-family: 'Poppins', sans-serif;
  font-size: 18px;
  font-weight: 600;
  line-height: 1;
  letter-spacing: 0.01em;
  text-transform: none; /* No ALL CAPS */
}
```

---

### Responsive Typography

```css
/* Fluid Typography (scales between mobile and desktop) */
.fluid-h1 {
  font-size: clamp(32px, 5vw, 60px);
}

.fluid-h2 {
  font-size: clamp(28px, 4vw, 48px);
}

.fluid-body {
  font-size: clamp(16px, 1.5vw, 18px);
}
```

---

## 🎭 LOGO & BRAND MARK

### Primary Logo

**Logo Type:** Wordmark + Animated Icon  
**Font:** Poppins Bold (700)  
**Icon:** Three animated dots (loading animation)

```html
<!-- Logo Structure -->
<div class="logo">
  <span class="logo-text">OLEKSIAK CONSULT</span>
  <div class="logo-dots">
    <span class="dot dot-1"></span>
    <span class="dot dot-2"></span>
    <span class="dot dot-3"></span>
  </div>
</div>
```

```css
/* Logo Styling */
.logo-text {
  font-family: 'Poppins', sans-serif;
  font-size: 24px;
  font-weight: 700;
  letter-spacing: 0.05em;
  color: #ffffff;
}

.logo-dots {
  display: inline-flex;
  gap: 4px;
  margin-left: 8px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: linear-gradient(135deg, #9333ea, #6b21a8);
  animation: pulse 1.5s ease-in-out infinite;
}

.dot-1 { animation-delay: 0s; }
.dot-2 { animation-delay: 0.2s; }
.dot-3 { animation-delay: 0.4s; }

@keyframes pulse {
  0%, 100% { 
    transform: scale(1); 
    opacity: 1; 
  }
  50% { 
    transform: scale(1.2); 
    opacity: 0.7; 
  }
}
```

---

### Logo Variations

#### Full Logo (Desktop Navigation)
- Text: "OLEKSIAK CONSULT"
- Size: 24px
- Color: White
- Animated dots: Always visible

#### Compact Logo (Mobile)
- Text: "O" + animated dots
- Size: 20px
- Used when space < 768px

#### Monochrome (Dark Backgrounds)
- All elements: White (#ffffff)
- Dots: White with opacity animation

#### Monochrome (Light Backgrounds)
- All elements: Moonlit Grey (#1a1a2e)
- Dots: Purple gradient maintained

---

### Logo Clear Space

**Minimum Clear Space:** 2x the height of the "O" letter

```
[--- 2x ---]  OLEKSIAK CONSULT  [--- 2x ---]
     ↑                                ↑
   Clear                           Clear
   Space                           Space
```

**Minimum Size:**
- Digital: 120px width (ensures legibility)
- Print: 40mm width

---

### Logo Don'ts

❌ **Do NOT:**
- Rotate the logo
- Change the font
- Separate the text from dots
- Change dot colors to anything other than purple gradient
- Outline the logo
- Apply drop shadows
- Distort proportions
- Place on busy backgrounds without backdrop filter

---

## 🎨 VISUAL STYLE

### Design Aesthetic: **Retro-Futuristic Tech**

Inspired by:
- Sci-fi interfaces (Blade Runner, Minority Report)
- CRT monitors and terminal screens
- 1980s neon aesthetics meets modern minimalism
- Glass morphism and depth effects
- Data visualization and dashboards

---

### Glass Morphism Effects

**Premium Cards:**
```css
.glass-card {
  background: linear-gradient(135deg, 
    rgba(147, 51, 234, 0.1) 0%, 
    rgba(59, 130, 246, 0.05) 100%);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px); /* Safari support */
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}
```

**Frosted Glass Overlay:**
```css
.frosted-glass {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(40px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.08);
}
```

---

### Shadow System

```css
/* Elevation System (Material Design inspired) */
--shadow-sm: 0 2px 4px rgba(0, 0, 0, 0.1);
--shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
--shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.2);
--shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.3);

/* Premium Shadows (with color glow) */
--shadow-purple-glow: 0 8px 32px rgba(147, 51, 234, 0.3);
--shadow-blue-glow: 0 8px 32px rgba(59, 130, 246, 0.3);

/* Double Shadow (depth effect) */
.premium-card {
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.3),
    0 0 0 1px rgba(255, 255, 255, 0.1);
}
```

---

### Border Radius System

```css
--radius-xs: 4px;    /* Small elements, badges */
--radius-sm: 8px;    /* Buttons, inputs */
--radius-md: 12px;   /* Cards, small containers */
--radius-lg: 16px;   /* Large cards, sections */
--radius-xl: 24px;   /* Hero sections, modals */
--radius-full: 9999px; /* Pills, avatars */
```

**Usage Guidelines:**
- **Buttons:** 8px (consistent with CTA prominence)
- **Cards:** 16px (premium feel)
- **Modals:** 24px (maximum depth)
- **Inputs:** 8px (matches buttons)

---

### Spacing System (8px Grid)

```css
/* Based on 8px increments */
--space-1: 8px;    /* 0.5rem */
--space-2: 16px;   /* 1rem */
--space-3: 24px;   /* 1.5rem */
--space-4: 32px;   /* 2rem */
--space-5: 40px;   /* 2.5rem */
--space-6: 48px;   /* 3rem */
--space-8: 64px;   /* 4rem */
--space-10: 80px;  /* 5rem */
--space-12: 96px;  /* 6rem */
--space-16: 128px; /* 8rem */
--space-20: 160px; /* 10rem */
```

**Component Spacing:**
- Section padding (vertical): 80px desktop, 48px mobile
- Card padding: 32px desktop, 24px mobile
- Button padding: 16px horizontal, 12px vertical
- Input padding: 16px

---

## 🧩 UI COMPONENTS

### Buttons

#### Primary CTA (Purple Gradient)
```css
.btn-primary {
  /* Layout */
  padding: 16px 32px;
  border-radius: 8px;
  
  /* Typography */
  font-family: 'Poppins', sans-serif;
  font-size: 18px;
  font-weight: 600;
  
  /* Colors */
  background: linear-gradient(135deg, #9333ea 0%, #6b21a8 100%);
  color: #ffffff;
  border: none;
  
  /* Effects */
  box-shadow: 0 4px 14px rgba(147, 51, 234, 0.4);
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(147, 51, 234, 0.6);
}

.btn-primary:active {
  transform: translateY(0);
}
```

#### Secondary CTA (Transparent with Border)
```css
.btn-secondary {
  padding: 16px 32px;
  border-radius: 8px;
  
  font-family: 'Poppins', sans-serif;
  font-size: 18px;
  font-weight: 600;
  
  background: transparent;
  color: #ffffff;
  border: 2px solid rgba(255, 255, 255, 0.3);
  
  transition: all 0.3s ease;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.5);
}
```

---

### Cards

#### Premium Glass Card (Services, Case Studies)
```css
.premium-card {
  /* Layout */
  padding: 40px;
  border-radius: 16px;
  
  /* Glass morphism */
  background: linear-gradient(135deg, 
    rgba(147, 51, 234, 0.1) 0%, 
    rgba(59, 130, 246, 0.05) 100%);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  
  /* Shadow */
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  
  /* Hover effect */
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.premium-card:hover {
  transform: translateY(-4px);
  box-shadow: 
    0 12px 40px rgba(0, 0, 0, 0.4),
    0 0 0 1px rgba(255, 255, 255, 0.15);
}
```

#### Methodology Card (LAMA Audit Section)
```css
.methodology-card {
  padding: 32px;
  border-radius: 12px;
  
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  
  /* Icon gradient background */
  .icon-wrapper {
    width: 56px;
    height: 56px;
    border-radius: 12px;
    background: linear-gradient(135deg, #9333ea 0%, #6b21a8 100%);
    display: flex;
    align-items: center;
    justify-content: center;
  }
}
```

---

### Forms

#### Input Field
```css
.input-field {
  /* Layout */
  width: 100%;
  padding: 16px;
  border-radius: 8px;
  
  /* Typography */
  font-family: 'DM Sans', sans-serif;
  font-size: 16px;
  color: #ffffff;
  
  /* Colors */
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.15);
  
  /* Focus state */
  transition: all 0.3s ease;
}

.input-field:focus {
  outline: none;
  border-color: #9333ea;
  box-shadow: 0 0 0 3px rgba(147, 51, 234, 0.2);
}

.input-field::placeholder {
  color: rgba(255, 255, 255, 0.3);
}
```

#### Checkbox (GDPR Consent)
```css
.checkbox-wrapper {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  
  input[type="checkbox"] {
    width: 20px;
    height: 20px;
    accent-color: #9333ea;
    cursor: pointer;
  }
  
  label {
    font-family: 'DM Sans', sans-serif;
    font-size: 14px;
    color: rgba(255, 255, 255, 0.7);
    line-height: 1.5;
  }
}
```

---

### Navigation

#### Desktop Navbar (Fixed Top)
```css
.navbar {
  position: fixed;
  top: 0;
  width: 100%;
  height: 80px;
  
  background: rgba(26, 26, 46, 0.9);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  
  z-index: 1000;
  
  nav ul {
    display: flex;
    gap: 32px;
    
    li a {
      font-family: 'Poppins', sans-serif;
      font-size: 16px;
      font-weight: 500;
      color: rgba(255, 255, 255, 0.8);
      transition: color 0.3s ease;
    }
    
    li a:hover {
      color: #ffffff;
    }
  }
}
```

#### Mobile Menu (Fullscreen Overlay)
```css
.mobile-menu {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100vh;
  
  background: rgba(26, 26, 46, 0.98);
  backdrop-filter: blur(20px);
  
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  
  nav ul {
    display: flex;
    flex-direction: column;
    gap: 32px;
    
    li a {
      font-family: 'Poppins', sans-serif;
      font-size: 24px;
      font-weight: 600;
      color: #ffffff;
    }
  }
}
```

---

## 🎬 MOTION & ANIMATION

### Animation Principles

1. **Purposeful** - Every animation serves a function
2. **Subtle** - Never distracting or overwhelming
3. **Performant** - Use `transform` and `opacity` only (GPU-accelerated)
4. **Consistent** - Same easing curves throughout

---

### Easing Functions

```css
/* Recommended easing (Material Design) */
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
--ease-out: cubic-bezier(0.0, 0, 0.2, 1);
--ease-in: cubic-bezier(0.4, 0, 1, 1);

/* Custom brand easing */
--ease-smooth: cubic-bezier(0.25, 0.1, 0.25, 1);
--ease-bounce: cubic-bezier(0.68, -0.55, 0.265, 1.55);
```

---

### Transition Timings

```css
--duration-fast: 150ms;     /* Hover states, micro-interactions */
--duration-base: 300ms;     /* Standard transitions */
--duration-slow: 500ms;     /* Complex animations */
--duration-slower: 800ms;   /* Page transitions */
```

---

### Signature Animations

#### Logo Dots Pulse
```css
@keyframes pulse {
  0%, 100% { 
    transform: scale(1); 
    opacity: 1; 
  }
  50% { 
    transform: scale(1.2); 
    opacity: 0.7; 
  }
}

.dot {
  animation: pulse 1.5s ease-in-out infinite;
}
```

#### Card Hover Lift
```css
.card {
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
}
```

#### CRT Shutdown Effect (Success Screen)
```css
@keyframes crtShutdown {
  0% {
    transform: scaleY(1);
    opacity: 1;
  }
  50% {
    transform: scaleY(0.01);
    opacity: 0.8;
  }
  100% {
    transform: scaleY(0);
    opacity: 0;
  }
}

.crt-effect {
  animation: crtShutdown 0.8s cubic-bezier(0.23, 1, 0.32, 1) forwards;
}
```

#### Typewriter Effect (Character-by-Character)
```typescript
// Custom React hook for typewriter
export function useTypewriter(text: string, speed: number = 25) {
  const [displayText, setDisplayText] = useState('');
  
  useEffect(() => {
    let index = 0;
    const timer = setInterval(() => {
      if (index < text.length) {
        setDisplayText(text.slice(0, index + 1));
        index++;
      } else {
        clearInterval(timer);
      }
    }, speed);
    
    return () => clearInterval(timer);
  }, [text, speed]);
  
  return displayText;
}
```

#### Floating Shapes (Background)
```css
@keyframes float {
  0%, 100% {
    transform: translate(0, 0) rotate(0deg);
  }
  25% {
    transform: translate(10px, -10px) rotate(5deg);
  }
  50% {
    transform: translate(-5px, 10px) rotate(-5deg);
  }
  75% {
    transform: translate(-10px, -5px) rotate(3deg);
  }
}

.floating-shape {
  animation: float 20s ease-in-out infinite;
  will-change: transform;
}
```

---

### Scroll-Triggered Animations

#### Fade In Up (Sections)
```css
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.fade-in-up {
  animation: fadeInUp 0.6s ease-out forwards;
  opacity: 0;
}
```

#### Intersection Observer Pattern
```typescript
// Lazy load sections on scroll
useEffect(() => {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('fade-in-up');
        }
      });
    },
    { threshold: 0.1 }
  );
  
  // Observe all sections
  document.querySelectorAll('.lazy-section').forEach((el) => {
    observer.observe(el);
  });
  
  return () => observer.disconnect();
}, []);
```

---

## 📸 IMAGERY & PHOTOGRAPHY

### Photography Style

**Aesthetic:** Minimalist, high-contrast, tech-forward

**Color Treatment:**
- Desaturated (-20% to -40% saturation)
- Cooler tones (blue/purple tint)
- High contrast (shadows: darker, highlights: brighter)
- Vignette effect (subtle)

**Subject Matter:**
- Modern offices (glass, steel, open spaces)
- Data visualizations (screens, dashboards)
- Abstract tech patterns
- Minimal portraits (professional, confident)

---

### Image Filters (CSS)

```css
/* Brand photo filter */
.brand-photo {
  filter: 
    saturate(0.6)          /* Desaturate 40% */
    contrast(1.2)          /* Increase contrast 20% */
    brightness(0.95)       /* Slightly darker */
    hue-rotate(10deg);     /* Purple tint */
}

/* Hover effect */
.brand-photo:hover {
  filter: 
    saturate(0.8)
    contrast(1.1)
    brightness(1);
  transition: filter 0.3s ease;
}
```

---

### Icon System

**Icon Library:** FontAwesome 6.x (Free Solid)

**Icon Style:**
- Solid fills (no outlines)
- Size: 24px default, 32px large, 48px XL
- Color: White or purple gradient

**Icon Wrapper (Gradient Background):**
```css
.icon-wrapper {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  background: linear-gradient(135deg, #9333ea 0%, #6b21a8 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  
  i {
    font-size: 24px;
    color: #ffffff;
  }
}
```

**Usage Examples:**
- Services: `faRocket`, `faEnvelope`, `faChartLine`, `faUsers`, `faChartBar`, `faChalkboardTeacher`
- LAMA Audit: `faSearch`, `faBolt`, `faBrain`, `faShieldHalved`, `faBullseye`, `faHeart`

---

## 🎤 CONTENT VOICE & TONE

### Brand Voice: **Confident Synthesizer**

**Core Attributes:**
- **Direct** - No fluff, straight to value
- **Data-Driven** - Numbers, metrics, ROI
- **Confident** - Proven results, not promises
- **ROI-Obsessed** - "Zawsze syntezuj" methodology
- **Approachable** - Human, not corporate

---

### Writing Principles

#### "Zawsze Syntezuj" (Always Synthesize)
❌ **DON'T:** "Here's your audit report with 47 data points..."  
✅ **DO:** "You're losing €X monthly. Fix these 3 gaps: A→B→C."

❌ **DON'T:** "Our comprehensive analysis revealed..."  
✅ **DO:** "I found the problem. Here's how to fix it."

---

### Messaging Framework

**Headlines:**
- Start with "I" (personal, accountable)
- Promise specific outcome
- Include metric when possible

**Examples:**
- "I turn underperforming CRM systems into your #1 revenue driver"
- "From 0.5% to 12%: Scaling Allegro's Automation Revenue"
- "I build CRM systems that retain 30% more customers"

**Subheadlines:**
- Explain HOW you deliver the promise
- Include timeframe when relevant
- Mention methodology

**Examples:**
- "From CRM strategy to marketing automation — I analyze your entire revenue pipeline and show you the gaps holding you back. Start with a free website audit."
- "I design email sequences that feel like 1-on-1 conversations. You'll convert 20-30% more prospects - automatically."

---

### Power Words

**Use frequently:**
- Revenue, ROI, Growth, Results, Measurable
- Double, Triple, 10x, 30%, 102% YoY
- Transform, Build, Scale, Optimize
- Proven, Guaranteed, Certified
- Systems, Frameworks, Methodology

**Avoid:**
- "Leverage", "Synergy", "Paradigm"
- "Best-in-class", "World-class" (show, don't tell)
- "Solutions", "Cutting-edge" (generic)
- Vague promises without metrics

---

### CTAs (Call-to-Actions)

**Format:** [Action Verb] + [Benefit/Outcome]

**Strong CTAs:**
- "Get Your Free Strategy Session →"
- "Yes, I Want to Double CRM Revenue →"
- "Book Free Consultation"
- "Get Free Website Audit ↓"

**Weak CTAs (avoid):**
- "Submit"
- "Learn More"
- "Contact Us"
- "Click Here"

---

## 💻 IMPLEMENTATION EXAMPLES

### Hero Section (Homepage)

```jsx
<section className="hero">
  <div className="container">
    <h1 className="hero-headline">
      I turn underperforming CRM systems into your #1 revenue driver
    </h1>
    
    <p className="hero-subheadline">
      From CRM strategy to marketing automation — I analyze your entire 
      revenue pipeline and show you the gaps holding you back. Start with 
      a free website audit.
    </p>
    
    <div className="hero-cta">
      <a href="https://calendly.com/..." className="btn-primary">
        Get Your Free Strategy Session →
      </a>
      <button className="btn-secondary" onClick={scrollToAudit}>
        Get Free Website Audit ↓
      </button>
    </div>
    
    <p className="hero-social-proof">
      ✓ Trusted by Allegro, Booksy, Accenture, McDonald's, and mBank 
      for CRM transformation
    </p>
  </div>
</section>
```

```css
.hero {
  min-height: 100vh;
  display: flex;
  align-items: center;
  background: linear-gradient(180deg, #1a1a2e 0%, #0f1419 100%);
  padding: 120px 0 80px;
}

.hero-headline {
  font-family: 'Poppins', sans-serif;
  font-size: clamp(32px, 5vw, 60px);
  font-weight: 700;
  line-height: 1.1;
  color: #ffffff;
  margin-bottom: 24px;
  max-width: 900px;
}

.hero-subheadline {
  font-family: 'DM Sans', sans-serif;
  font-size: clamp(16px, 1.5vw, 20px);
  line-height: 1.7;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 40px;
  max-width: 600px;
}

.hero-cta {
  display: flex;
  gap: 16px;
  margin-bottom: 32px;
}

.hero-social-proof {
  font-family: 'DM Sans', sans-serif;
  font-size: 16px;
  color: rgba(255, 255, 255, 0.6);
}
```

---

### Service Card (Glass Morphism)

```jsx
<div className="service-card">
  <div className="service-icon">
    <FontAwesomeIcon icon={faRocket} />
  </div>
  
  <h3 className="service-title">
    CRM Strategy That Retains 30% More Customers
  </h3>
  
  <p className="service-description">
    I build CRM systems that turn one-time buyers into repeat customers. 
    My proven frameworks help you retain 20-30% more customers than 
    industry average.
  </p>
  
  <ul className="service-features">
    <li>HubSpot, Salesforce, Pipedrive setup</li>
    <li>Custom workflow automation (15+ hours saved/week)</li>
    <li>Lead scoring & segmentation</li>
  </ul>
</div>
```

```css
.service-card {
  padding: 40px;
  border-radius: 16px;
  
  background: linear-gradient(135deg, 
    rgba(147, 51, 234, 0.1) 0%, 
    rgba(59, 130, 246, 0.05) 100%);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.service-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
}

.service-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  background: linear-gradient(135deg, #9333ea 0%, #6b21a8 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24px;
  
  svg {
    font-size: 24px;
    color: #ffffff;
  }
}

.service-title {
  font-family: 'Poppins', sans-serif;
  font-size: 24px;
  font-weight: 700;
  color: #ffffff;
  margin-bottom: 16px;
}

.service-description {
  font-family: 'DM Sans', sans-serif;
  font-size: 16px;
  line-height: 1.7;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 24px;
}

.service-features {
  list-style: none;
  
  li {
    font-family: 'DM Sans', sans-serif;
    font-size: 14px;
    color: rgba(255, 255, 255, 0.6);
    margin-bottom: 12px;
    padding-left: 24px;
    position: relative;
    
    &::before {
      content: "•";
      position: absolute;
      left: 8px;
      color: #9333ea;
      font-size: 20px;
    }
  }
}
```

---

### Case Study Card (Results-Focused)

```jsx
<div className="case-study-card">
  <div className="case-study-header">
    <div className="client-logo">ALLEGRO</div>
    <span className="metric-badge">+11.5pp</span>
  </div>
  
  <h3 className="case-study-title">
    From 0.5% to 12%: Scaling Allegro's Automation Revenue
  </h3>
  
  <div className="case-study-challenge">
    <strong>CHALLENGE:</strong> Allegro's marketing automation generated 
    just 0.5% of total revenue despite €50M+ investment.
  </div>
  
  <div className="case-study-result">
    <strong>RESULT:</strong> Scaled automation from 0.5% to 12% revenue 
    contribution in 18 months. Built 15-person team. Managed $2M budget.
  </div>
  
  <div className="case-study-metrics">
    <div className="metric">
      <span className="metric-value">102%</span>
      <span className="metric-label">YoY Growth</span>
    </div>
    <div className="metric">
      <span className="metric-value">$2M</span>
      <span className="metric-label">Budget</span>
    </div>
    <div className="metric">
      <span className="metric-value">15</span>
      <span className="metric-label">Team Size</span>
    </div>
  </div>
</div>
```

---

## ✅ DO'S AND DON'TS

### Typography

✅ **DO:**
- Use Poppins for headlines, DM Sans for body
- Maintain 1.1-1.2 line-height for headlines
- Maintain 1.7 line-height for body copy
- Use fluid typography: `clamp()`
- Keep headline length under 60 characters

❌ **DON'T:**
- Mix more than 2 font families
- Use ALL CAPS for long text
- Go below 16px for body text on mobile
- Use tight letter-spacing (<-0.03em)

---

### Color

✅ **DO:**
- Use purple gradient for primary CTAs
- Maintain WCAG AA contrast ratios (4.5:1 minimum)
- Use glass morphism for premium cards
- Apply color glow to shadows on CTAs
- Use white text on dark backgrounds

❌ **DON'T:**
- Use pure black (#000000) - always use Moonlit Grey
- Mix more than 3 accent colors per section
- Use color as the only differentiator (accessibility)
- Apply gradients to body text (readability)

---

### Layout

✅ **DO:**
- Use 8px spacing grid
- Maintain consistent card padding (40px desktop, 24px mobile)
- Use 80px navbar height (desktop)
- Add ample white space (70% content, 30% whitespace)
- Use responsive grid: 1/2/3 columns based on viewport

❌ **DON'T:**
- Use arbitrary spacing values (15px, 23px, etc.)
- Crowd elements together (minimum 16px gap)
- Create layouts wider than 1440px (max-width)
- Forget mobile breakpoints at 768px, 1024px

---

### Animation

✅ **DO:**
- Use `transform` and `opacity` for performance
- Keep animations under 800ms (except page transitions)
- Use easing curves (cubic-bezier)
- Add `will-change: transform` for smooth animations
- Provide `prefers-reduced-motion` fallbacks

❌ **DON'T:**
- Animate `width`, `height`, `top`, `left` (causes reflow)
- Create animations longer than 1 second
- Use linear easing (looks mechanical)
- Animate too many elements at once
- Forget mobile performance (animations cost more)

---

### Content

✅ **DO:**
- Start headlines with "I" (personal accountability)
- Include specific metrics (30%, 102% YoY, €X)
- Use "You" to address the reader
- Keep sentences under 20 words
- Use bullet points for lists (not paragraphs)

❌ **DON'T:**
- Use corporate jargon ("leverage", "synergy")
- Make vague claims ("best-in-class")
- Write paragraphs longer than 3 sentences
- Use passive voice ("Results were achieved")

---

## 📦 BRAND ASSETS CHECKLIST

### Essential Files

- [ ] Logo (SVG) - Primary wordmark + animated dots
- [ ] Logo (PNG) - 512x512px, transparent background
- [ ] Favicon (ICO) - 32x32px, 16x16px
- [ ] Fonts (WOFF2) - Poppins (400, 600, 700, 900), DM Sans (400, 500, 700)
- [ ] Color Palette (CSS Variables) - All brand colors
- [ ] Component Library (Storybook) - All UI components documented

### Documentation

- [ ] This Brand Guidelines document (BRAND_GUIDELINES.md)
- [ ] Visual Style Guide (PDF) - For print/external use
- [ ] Component Documentation (Storybook) - For developers
- [ ] Content Style Guide - Voice, tone, messaging

---

## 🔄 VERSION HISTORY

**Version 1.0** (January 4, 2026)
- Initial brand guidelines created
- Color system, typography, logo, visual style defined
- UI components, motion system, content voice documented
- Implementation examples and do's/don'ts added

---

## 📞 BRAND INQUIRIES

For questions about brand usage, adaptations, or custom applications:

**Contact:** Rafał Oleksiak  
**Email:** rafal@oleksiakconsulting.com  
**Website:** https://oleksiakconsulting.com

---

**END OF BRAND GUIDELINES**

*This document serves as the single source of truth for visual identity implementation across all Rafał Oleksiak Consulting digital properties. All developers, designers, and collaborators should reference this guide to maintain brand consistency.*
