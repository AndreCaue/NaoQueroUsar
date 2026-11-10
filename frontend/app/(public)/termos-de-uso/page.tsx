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

          <h2 className="text-3xl font-semibold border-b border-gray-700 pb-4 mb-8">
            TERMOS DE USO
          </h2>
        </header>

        <article className="prose lg:prose-xl text-base leading-relaxed">
          <p>Última atualização: 9 de novembro de 2026</p>

          <h3 className="text-xl font-bold my-2 underline">1. Objeto</h3>
          <p>
            O site <strong>NQU</strong> tem como finalidade exclusiva a
            divulgação de oportunidades de emprego e a facilitação do contato
            entre candidatos e recrutadores/empresas. O NQU não realiza
            processos seletivos, não intermediaria contratações e não atua como
            agência de emprego.
          </p>

          <h3 className="text-xl font-bold my-2 underline">
            2. Natureza do serviço
          </h3>
          <p>
            O NQU atua apenas como plataforma de divulgação. As vagas publicadas
            são obtidas a partir de grupos públicos ou semi-públicos de
            WhatsApp, sendo processadas e reescritas antes da publicação.
          </p>
          <p>
            Não garantimos a veracidade, atualidade ou legitimidade das vagas,
            nem o resultado de qualquer processo seletivo. O contato com
            recrutadores ou empresas é de inteira responsabilidade do usuário.
          </p>

          <h3 className="text-xl font-bold my-2 underline">
            3. Uso do site e responsabilidades do usuário
          </h3>
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

          <h3 className="text-xl font-bold my-2 underline">
            4. Publicação de vagas
          </h3>
          <p>
            As vagas são publicadas exclusivamente pela administração do site.
            Não há, no momento, funcionalidade de publicação de vagas por
            usuários ou empresas.
          </p>
          <p>
            As vagas permanecem disponíveis por 14 dias e são excluídas de forma
            definitiva após esse período.
          </p>

          <h3 className="text-xl font-bold my-2 underline">
            5. Propriedade intelectual
          </h3>
          <p>
            Todo o conteúdo do site (textos, layout, código, design e demais
            elementos) é de propriedade do NQU ou de seus licenciadores. É
            proibida a cópia, reprodução, distribuição ou qualquer forma de uso
            não autorizado.
          </p>

          <h3 className="text-xl font-bold my-2 underline">
            6. Limitação de responsabilidade
          </h3>
          <p>
            Na máxima extensão permitida pela legislação brasileira, o NQU e seu
            operador não se responsabilizam por:
          </p>
          <ul className="list-disc pl-5 mb-6">
            <li>
              Danos decorrentes do uso do site ou da impossibilidade de uso;
            </li>
            <li>Conteúdo, veracidade ou legalidade das vagas publicadas;</li>
            <li>
              Interações, acordos ou problemas ocorridos entre candidatos e
              recrutadores/empresas;
            </li>
            <li>
              Eventuais prejuízos causados por informações de contato incorretas
              ou desatualizadas.
            </li>
          </ul>

          <h3 className="text-xl font-bold my-2 underline">7. Privacidade</h3>
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

          <h3 className="text-xl font-bold my-2 underline">8. Alterações</h3>
          <p>
            Estes Termos de Uso podem ser atualizados a qualquer momento. A
            versão mais recente estará sempre disponível nesta página. O uso
            continuado do site após a publicação de alterações implica aceitação
            da nova versão.
          </p>

          <h3 className="text-xl font-bold my-2 underline">9. Foro</h3>
          <p>
            Fica eleito o foro da comarca de Americana, Estado de São Paulo,
            para dirimir quaisquer controvérsias oriundas destes Termos de Uso,
            com renúncia a qualquer outro, por mais privilegiado que seja.
          </p>

          <h3 className="text-xl font-bold my-2 underline">10. Contato</h3>
          <p>
            Dúvidas sobre estes Termos de Uso podem ser enviadas para:{" "}
            <strong>suportenqs@outlook.com</strong>
          </p>
        </article>
      </div>
    </main>
  );
}
