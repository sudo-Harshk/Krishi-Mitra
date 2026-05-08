export function Hero() {
  return (
    <section className="hero">
      <div className="hero-copy">
        <p className="eyebrow">Krishi Mitra</p>
        <h1>Crop diagnosis, made simple.</h1>
        <p className="lead">
          Describe the issue, add a photo if you have one, and get a structured
          English and Telugu response that is easy to scan on a phone.
        </p>
        <div className="hero-points" aria-label="Product highlights">
          <span>Mobile-first</span>
          <span>Bilingual</span>
          <span>Weather-aware</span>
        </div>
      </div>

      <div className="hero-visual" aria-hidden="true">
        <div className="visual-card visual-card-top">
          <span className="visual-label">Input</span>
          <strong>Crop photo + description</strong>
        </div>
        <div className="visual-card visual-card-bottom">
          <span className="visual-label">Output</span>
          <strong>Diagnosis + actions + caution</strong>
        </div>
      </div>
    </section>
  );
}

