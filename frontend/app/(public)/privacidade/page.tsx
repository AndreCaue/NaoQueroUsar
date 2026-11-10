/* eslint-disable */
/* import.meta disable */

export default function PrivacidadePage() {
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
                    href="/termos-de-uso"
                    className="hover:text-accent-strong transition-colors"
                  >
                    Termos de Uso
                  </a>
                </li>
              </ul>
            </nav>
          </div>

          <h2 className="text-3xl font-semibold border-b border-gray-700 pb-4 mb-8">
            POLÍTICA DE PRIVACIDADE
          </h2>
        </header>

        <article className="prose lg:prose-xl text-base leading-relaxed">
          <p>Última atualização: 9 de novembro de 2026</p>

          <h3 className="text-xl font-bold my-2 underline">1. Quem somos</h3>
          <p>
            O site <strong>NQU</strong> é operado por{" "}
            <strong>André Cauê G.C</strong>, pessoa física, com o objetivo de
            divulgar oportunidades de emprego e facilitar o contato entre
            candidatos e recrutadores/empresas.
          </p>

          <h3 className="text-xl font-bold my-2 underline">
            2. Quais dados tratamos
          </h3>
          <p>
            Atualmente, o NQU{" "}
            <strong>
              não solicita nem coleta dados pessoais de candidatos
            </strong>{" "}
            (não há cadastro, envio de currículo ou formulário de candidatura).
          </p>
          <p>Os dados tratados são:</p>
          <ul className="list-disc pl-5 mb-6">
            <li>
              <strong>Dados de navegação (técnicos)</strong>: endereço IP, tipo
              de navegador, páginas acessadas e informações de segurança, quando
              necessários para o funcionamento e proteção do site.
            </li>
            <li>
              <strong>Dados contidos nas vagas</strong>: título da vaga,
              descrição, cidade, benefícios e informações de contato (telefone
              e/ou e-mail) do recrutador ou empresa responsável.
            </li>
            <li>
              <strong>Cookies e tecnologias similares</strong>: caso o Google
              Analytics seja utilizado, serão coletados dados de navegação de
              forma agregada para análise de tráfego.
            </li>
          </ul>

          <h3 className="text-xl font-bold my-2 underline">
            3. Origem dos dados das vagas
          </h3>
          <p>
            As vagas publicadas no NQU são obtidas a partir de grupos públicos
            ou semi-públicos de WhatsApp. Os textos são processados e reescritos
            antes da publicação. Apenas a versão elaborada fica armazenada no
            site. As vagas não são cópia integral das mensagens originais.
          </p>

          <h3 className="text-xl font-bold my-2 underline">
            4. Finalidade do tratamento
          </h3>
          <p>Os dados são tratados exclusivamente para:</p>
          <ul className="list-disc pl-5 mb-6">
            <li>Divulgar oportunidades de emprego;</li>
            <li>
              Permitir que candidatos visualizem as vagas e, mediante validação
              anti-bot, acessem o contato do recrutador/empresa;
            </li>
            <li>Garantir a segurança e o bom funcionamento do site;</li>
            <li>
              Analisar o uso do site de forma agregada (caso o Google Analytics
              seja utilizado);
            </li>
            <li>Cumprir obrigações legais.</li>
          </ul>

          <h3 className="text-xl font-bold my-2 underline">5. Base legal</h3>
          <p>
            O tratamento dos dados se fundamenta principalmente no{" "}
            <strong>legítimo interesse</strong> (divulgação de oportunidades de
            emprego e funcionamento do site) e, quando aplicável, no
            consentimento (ex.: cookies não essenciais).
          </p>

          <h3 className="text-xl font-bold my-2 underline">
            6. Compartilhamento de dados
          </h3>
          <ul className="list-disc pl-5 mb-6">
            <li>
              Os dados de contato das vagas ficam disponíveis publicamente no
              site após o usuário passar pela validação anti-bot.
            </li>
            <li>Não vendemos, alugamos ou comercializamos dados pessoais.</li>
            <li>
              Dados técnicos podem ser processados por prestadores de serviço
              necessários ao funcionamento do site (hospedagem e banco de
              dados).
            </li>
          </ul>

          <h3 className="text-xl font-bold my-2 underline">
            7. Transferência internacional de dados
          </h3>
          <p>
            O site utiliza serviços de infraestrutura localizados fora do Brasil
            (atualmente Vercel e Neon). Dessa forma, dados técnicos de navegação
            e os dados das vagas podem ser processados em servidores localizados
            no exterior. Adotamos medidas para que esse tratamento ocorra de
            forma segura.
          </p>

          <h3 className="text-xl font-bold my-2 underline">
            8. Cookies e Google Analytics
          </h3>
          <p>
            Caso o Google Analytics seja implementado, utilizaremos cookies e
            tecnologias semelhantes para entender como os visitantes utilizam o
            site. Você poderá gerenciar suas preferências de cookies por meio
            das configurações do seu navegador.
          </p>

          <h3 className="text-xl font-bold my-2 underline">
            9. Retenção dos dados
          </h3>
          <ul className="list-disc pl-5 mb-6">
            <li>
              <strong>Vagas</strong>: permanecem publicadas por 14 dias contados
              da data de publicação. Após esse período, são excluídas de forma
              definitiva (hard delete).
            </li>
            <li>
              <strong>Dados de navegação e logs técnicos</strong>: mantidos pelo
              tempo necessário para segurança e funcionamento do site.
            </li>
            <li>
              Não armazenamos dados de candidatura, pois essa funcionalidade
              ainda não existe.
            </li>
          </ul>

          <h3 className="text-xl font-bold my-2 underline">
            10. Direitos do titular
          </h3>
          <p>
            Nos termos da Lei Geral de Proteção de Dados (LGPD), você pode
            solicitar:
          </p>
          <ul className="list-disc pl-5 mb-6">
            <li>Confirmação da existência de tratamento;</li>
            <li>Acesso aos dados;</li>
            <li>Correção de dados incompletos ou desatualizados;</li>
            <li>Eliminação dos dados;</li>
            <li>Portabilidade (quando aplicável);</li>
            <li>Informação sobre compartilhamento;</li>
            <li>Revogação de consentimento;</li>
            <li>Oposição ao tratamento.</li>
          </ul>
          <p>
            Para exercer esses direitos, envie um e-mail para:{" "}
            <strong>suportenqs@outlook.com</strong>
          </p>

          <h3 className="text-xl font-bold my-2 underline">11. Segurança</h3>
          <p>
            Adotamos medidas técnicas e organizacionais razoáveis para proteger
            os dados contra acessos não autorizados, perda, alteração ou
            qualquer forma de tratamento inadequado.
          </p>

          <h3 className="text-xl font-bold my-2 underline">
            12. Alterações desta Política
          </h3>
          <p>
            Esta Política de Privacidade poderá ser atualizada periodicamente. A
            versão mais recente estará sempre disponível nesta página, com a
            data da última atualização.
          </p>

          <h3 className="text-xl font-bold my-2 underline">13. Contato</h3>
          <p>
            Dúvidas sobre esta Política ou sobre o tratamento de dados pessoais
            podem ser enviadas para: <strong>suportenqs@outlook.com</strong>
          </p>
        </article>
      </div>
    </main>
  );
}
