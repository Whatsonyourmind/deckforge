/**
 * Fluent PresentationBuilder -- immutable builder for constructing typed PresentationIR.
 *
 * Every mutation method returns a NEW builder instance (immutable pattern),
 * so callers can branch without side effects.
 *
 * @example
 * ```typescript
 * const ir = Presentation.create("Q4 Earnings")
 *   .theme("corporate_dark")
 *   .metadata({ audience: "board", purpose: "quarterly_review" })
 *   .addSlide(Slide.title({ title: "Q4 2025 Earnings", subtitle: "Confidential" }))
 *   .addSlide(Slide.bullets({ title: "Highlights", items: ["Revenue +12%", "EBITDA +8%"] }))
 *   .build();
 * ```
 */

import type {
  BrandKit,
  GenerationOptions,
  PresentationIR,
  PresentationMetadata,
  SlideInput,
} from "../types";

export class PresentationBuilder {
  private readonly _title: string;
  private readonly _theme?: string;
  private readonly _metadata: Partial<PresentationMetadata>;
  private readonly _brandKit?: BrandKit;
  private readonly _slides: readonly SlideInput[];
  private readonly _generationOptions?: Partial<GenerationOptions>;

  private constructor(init: {
    title: string;
    theme?: string;
    metadata?: Partial<PresentationMetadata>;
    brandKit?: BrandKit;
    slides?: readonly SlideInput[];
    generationOptions?: Partial<GenerationOptions>;
  }) {
    this._title = init.title;
    this._theme = init.theme;
    this._metadata = init.metadata ?? {};
    this._brandKit = init.brandKit;
    this._slides = init.slides ?? [];
    this._generationOptions = init.generationOptions;
  }

  /** Create a new PresentationBuilder with the given title. */
  static create(title: string): PresentationBuilder {
    return new PresentationBuilder({ title });
  }

  /** Set the theme identifier. Returns a new builder. */
  theme(themeId: string): PresentationBuilder {
    return new PresentationBuilder({
      title: this._title,
      theme: themeId,
      metadata: this._metadata,
      brandKit: this._brandKit,
      slides: this._slides,
      generationOptions: this._generationOptions,
    });
  }

  /** Merge additional metadata fields. Returns a new builder. */
  metadata(meta: Partial<PresentationMetadata>): PresentationBuilder {
    return new PresentationBuilder({
      title: this._title,
      theme: this._theme,
      metadata: { ...this._metadata, ...meta },
      brandKit: this._brandKit,
      slides: this._slides,
      generationOptions: this._generationOptions,
    });
  }

  /** Set the brand kit. Returns a new builder. */
  brandKit(kit: BrandKit): PresentationBuilder {
    return new PresentationBuilder({
      title: this._title,
      theme: this._theme,
      metadata: this._metadata,
      brandKit: kit,
      slides: this._slides,
      generationOptions: this._generationOptions,
    });
  }

  /** Append a single slide. Returns a new builder. */
  addSlide(slide: SlideInput): PresentationBuilder {
    return new PresentationBuilder({
      title: this._title,
      theme: this._theme,
      metadata: this._metadata,
      brandKit: this._brandKit,
      slides: [...this._slides, slide],
      generationOptions: this._generationOptions,
    });
  }

  /** Append multiple slides. Returns a new builder. */
  addSlides(slides: SlideInput[]): PresentationBuilder {
    return new PresentationBuilder({
      title: this._title,
      theme: this._theme,
      metadata: this._metadata,
      brandKit: this._brandKit,
      slides: [...this._slides, ...slides],
      generationOptions: this._generationOptions,
    });
  }

  /** Set generation options. Returns a new builder. */
  generationOptions(opts: Partial<GenerationOptions>): PresentationBuilder {
    return new PresentationBuilder({
      title: this._title,
      theme: this._theme,
      metadata: this._metadata,
      brandKit: this._brandKit,
      slides: this._slides,
      generationOptions: { ...this._generationOptions, ...opts },
    });
  }

  /**
   * Validate and build the final PresentationIR.
   * Throws if no slides have been added.
   */
  build(): PresentationIR {
    if (this._slides.length === 0) {
      throw new Error(
        "PresentationBuilder: at least one slide is required. Use .addSlide() before .build().",
      );
    }

    const ir: PresentationIR = {
      schema_version: "1.0",
      metadata: {
        title: this._title,
        ...this._metadata,
      },
      slides: [...this._slides],
    };

    if (this._theme !== undefined) {
      ir.theme = this._theme;
    }

    if (this._brandKit !== undefined) {
      ir.brand_kit = this._brandKit;
    }

    if (this._generationOptions !== undefined) {
      ir.generation_options = this._generationOptions as PresentationIR["generation_options"];
    }

    return ir;
  }

  /**
   * Build the IR and render it using the given DeckForge client.
   * Convenience shorthand for `client.render(builder.build())`.
   */
  async render(client: { render: (ir: PresentationIR) => Promise<unknown> }) {
    return client.render(this.build());
  }

  /**
   * Build the IR and estimate cost using the given DeckForge client.
   * Convenience shorthand for `client.estimate(builder.build())`.
   */
  async estimate(client: { estimate: (ir: PresentationIR) => Promise<unknown> }) {
    return client.estimate(this.build());
  }
}

/**
 * Namespace alias for PresentationBuilder.create().
 * Provides a shorter entry point: `Presentation.create("Title")`.
 */
export const Presentation = {
  create: PresentationBuilder.create,
} as const;
