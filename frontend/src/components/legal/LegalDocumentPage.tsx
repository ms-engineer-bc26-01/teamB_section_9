type LegalSection = {
  title: string;
  body: string[];
};

type LegalDocumentPageProps = {
  title: string;
  lead: string;
  updatedAt: string;
  sections: LegalSection[];
};

export function LegalDocumentPage({
  title,
  lead,
  updatedAt,
  sections,
}: LegalDocumentPageProps) {
  return (
    <article className="space-y-8 pb-8">
      <header className="space-y-3">
        <p className="text-sm font-medium text-[#8C715C]">Climo</p>
        <div className="space-y-2">
          <h1 className="text-2xl font-bold leading-tight text-[#2B2926]">
            {title}
          </h1>
          <p className="text-sm leading-6 text-[#6F6258]">{lead}</p>
        </div>
        <p className="text-xs text-[#8C715C]">最終更新日: {updatedAt}</p>
      </header>

      <div className="space-y-6">
        {sections.map((section) => (
          <section key={section.title} className="space-y-3">
            <h2 className="text-base font-bold leading-7 text-[#2B2926]">
              {section.title}
            </h2>
            <div className="space-y-2 text-sm leading-7 text-[#4B3A2F]">
              {section.body.map((paragraph) => (
                <p key={paragraph}>{paragraph}</p>
              ))}
            </div>
          </section>
        ))}
      </div>
    </article>
  );
}
