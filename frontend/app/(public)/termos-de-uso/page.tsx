/* eslint-disable */
/* import.meta disable */

import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Termos de Uso — EmpregaNoix",
  description:
    "Termos de uso da plataforma EmpregaNoix. Regras para uso do site e da plataforma de vagas.",
};

export default function TermosDeUsoPage() {
  return (
    <main className="min-h-screen bg-canvas text-fg">
      <div className="max-w-3xl mx-auto px-4 py-12">
        <header className="mb-12">
          <div className="flex items-center justify-between mb-8">
            <span className="text-2xl font-bold">EmpregaNoix</span>
            <nav>
              <ul className="flex gap-6 text-sm">
                <li>
                  <a
                    href="/admin/paste"
                    className="hover:text-accent-strong transition-colors"
                  >
                    Painel Admin
                  </a>
                </li>
                <li>
                  <a
                    href="/privacidade"
                    className="hover:text-accent-strong transition-colors"
                  >
                    Política de Privacidade
                  </a>
                </li>
              </ul>
            </nav>
          </div>

          <h1 className="text-3xl font-semibold border-b border-line pb-4 mb-8">
            TERMOS DE USO
          </h1>
        </header>

        <article className="prose lg:prose-xl text-base leading-relaxed">
          <p>Última atualização: 9 de novembro de 2026</p>

          <h2 className="text-xl font-bold my-2 underline">1. Objeto</h2>
          <p>
            O site <strong>EmpregaNoix</strong> tem como finalidade exclusiva a
            divulgação de oportunidades de emprego e a facilitação do contato
            entre candidatos e recrutadores/empresas. O EmpregaNoix não realiza
            processos seletivos, não intermediaria contratações e não atua como
            agência de emprego.
          </p>

          <h2 className="text-xl font-bold my-2 underline">
            2. Natureza do serviço
          </h2>
          <p>
            O EmpregaNoix atua apenas como plataforma de divulgação. As vagas publicadas
            são obtidas a partir de grupos públicos ou semi-públicos de
            WhatsApp, sendo processadas e reescritas antes da publicação.
          </p>
          <p>
            Não garantimos a veracidade, atualidade ou legitimidade das vagas,
            nem o resultado de qualquer processo seletivo. O contato com
            recrutadores ou empresas é de inteira responsabilidade do usuário.
          </p>

          <h2 className="text-xl font-bold my-2 underline">
            3. Uso do site e responsabilidades do usuário
          </h2>
          <ul className="list-disc pl-5 mb-6">
            <li>
              O usuário se compromete a utilizar o site de forma legítima e de
              acordo com a legislação vigente.
            </li>
            <li>
              É proibido o uso de bots, scripts, automações ou qualquer meio
              automatizado para acessar contatos, coletar dados ou sobrecarregar
              o sistema.
            </li>
            <li>
              É proibido utilizar as informações de contato obtidas no site para
              fins de spam, assédio, cobrança indevida ou qualquer atividade
              ilícita.
            </li>
            <li>
              O usuário é o único responsável pelas interações realizadas com
              recrutadores e empresas a partir dos contatos divulgados.
            </li>
          </ul>

          <h2 className="text-xl font-bold my-2 underline">
            4. Publicação de vagas
          </h2>
          <p>
            As vagas são publicadas exclusivamente pela administração do site.
            Não há, no momento, funcionalidade de publicação de vagas por
            usuários ou empresas.
          </p>
          <p>
            As vagas permanecem disponíveis por 14 dias e são excluídas de forma
            definitiva após esse período.
          </p>

          <h2 className="text-xl font-bold my-2 underline">
            5. Propriedade intelectual
          </h2>
          <p>
            Todo o conteúdo do site (textos, layout, código, design e demais
            elementos) é de propriedade do EmpregaNoix ou de seus licenciadores. É
            proibida a cópia, reprodução, distribuição ou qualquer forma de uso
            não autorizado.
          </p>

          <h2 className="text-xl font-bold my-2 underline">
            6. Limitação de responsabilidade
          </h2>
          <p>
            Na máxima extensão permitida pela legislação brasileira, o EmpregaNoix e seu
            operador não se responsabilizam por:
          </p>
          <ul className="list-disc pl-5 mb-6">
            <li>
              Danos decorrentes do uso do site ou da impossibilidade de uso;
            </li>
            <li>
              Conteúdo, veracidade ou legalidade das vagas publicadas;
            </li>
            <li>
              Interações, acordos ou problemas ocorridos entre candidatos e
              recrutadores/empresas;
            </li>
            <li>
              Eventuais prejuízos causados por informações de contato incorretas
              ou desatualizadas.
            </li>
          </ul>

          <h2 className="text-xl font-bold my-2 underline">
            7. Privacidade
          </h2>
          <p>
            O tratamento de dados pessoais é regido pela nossa{" "}
            <a
              href="/privacidade"
              className="text-accent-strong hover:underline"
            >
              Política de Privacidade
            </a>
            .
          </p>

          <h2 className="text-xl font-bold my-2 underline">
            8. Alterações
          </h2>
          <p>
            Estes Termos de Uso podem ser atualizados a qualquer momento. A
            versão mais recente estará sempre disponível nesta página. O uso
            continuado do site após a publicação de alterações implica aceitação
            da nova versão.
          </p>

          <h2 className="text-xl font-bold my-2 underline">
            9. Foro
          </h2>
          <p>
            Fica eleito o foro da comarca de Americana, Estado de São Paulo,
            para dirimir quaisquer controvérsias oriundas destes Termos de Uso,
            com renúncia a qualquer outro, por mais privilegiado que seja.
          </p>

          <h2 className="text-xl font-bold my-2 underline">
            10. Contato
          </h2>
          <p>
            Dúvidas sobre estes Termos de Uso podem ser enviadas para:{" "}
            <strong>empreganoix@outlook.com</strong>
          </p>
        </article>

        {/* Required LGPD notice — verbatim */}
        <div className="mt-12 p-6 bg-surface border border-line rounded-md mb-8">
          <p className="text-sm text-fg-muted">
            Somos apenas meio de divulgação. As vagas são obtidas de grupos
            públicos de WhatsApp e o contato é disponibilizado após validação
            anti-bot. Não armazenamos dados de candidatura e não nos
            responsabilizamos por interações entre candidatos e empresas.
          </p>
        </div>
      </div>
    </main>
  );
}