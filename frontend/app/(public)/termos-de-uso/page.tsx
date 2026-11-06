/* eslint-disable */
/* import.meta disable */

export default function TermosDeUsoPage() {
  return (
    <main className="min-h-screen bg-gray-900 text-white">
      <div className="max-w-3xl mx-auto px-4 py-12">
        <header className="mb-12">
          <div className="flex items-center justify-between mb-8">
            <span className="text-2xl font-bold">NQU</span>
            <nav>
              <ul className="flex gap-6 text-sm">
                <li>
                  <a href="/admin/paste" className="hover:text-accent-strong transition-colors">Painel Admin</a>
                </li>
                <li>
                  <a href="/privacidade" className="hover:text-accent-strong transition-colors">Política de Privacidade</a>
                </li>
              </ul>
            </nav>
          </div>

          <h2 className="text-3xl font-semibold border-b border-gray-700 pb-4 mb-8">TERMOS DE USO</h2>
        </header>

        <article className="prose lg:prose-xl text-lg leading-relaxed">
          <p>Última atualização: quinta-feira, 5 de novembro de 2026</p>

          <h3>1. Objeto</h3>
          <p>O site tem como finalidade exclusiva a divulgação de vagas de emprego e a intermediação entre candidatos e empresas.</p>

          <h3>2. Cadastro e responsabilidades</h3>
          <ul className="list-disc pl-5 mb-6">
            <li>Os usuários são responsáveis pela veracidade das informações fornecidas.</li>
            <li>É proibido publicar vagas falsas, discriminatórias ou que violem a legislação.</li>
            <li>Candidatos devem se candidatar de forma legítima, sem uso de bots ou automatizações abusivas.</li>
          </ul>

          <h3>3. Natureza do serviço</h3>
          <p>O site atua apenas como intermediário. Não garantimos a contratação, a veracidade das vagas ou o resultado de qualquer processo seletivo.</p>

          <h3>4. Propriedade intelectual</h3>
          <p>Todo o conteúdo do site (textos, layout, código etc.) é protegido. É proibida a cópia ou reprodução sem autorização.</p>

          <h3>5. Limitação de responsabilidade</h3>
          <p>Na máxima extensão permitida por lei, não nos responsabilizamos por danos decorrentes do uso do site, de interações entre usuários ou de informações publicadas por terceiros.</p>

          <h3>6. Privacidade</h3>
          <p>O tratamento de dados pessoais é regido pela nossa <a href="/privacidade">Política de Privacidade</a>.</p>

          <h3>7. Alterações</h3>
          <p>Podemos alterar estes Termos a qualquer momento. O uso continuado do site após a alteração implica aceitação da nova versão.</p>

          <h3>8. Foro</h3>
          <p>Fica eleito o foro da comarca de [sua cidade/estado] para dirimir quaisquer controvérsias.</p>
        </article>
      </div>
    </main>
  );
}