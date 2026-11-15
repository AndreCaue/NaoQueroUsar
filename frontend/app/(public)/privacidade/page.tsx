import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Política de Privacidade — EmpregaNoix",
  description:
    "Política de Privacidade do EmpregaNoix: quais dados são tratados, base legal, retenção de 14 dias das vagas e direitos do titular sob a LGPD.",
};

export default function PrivacidadePage() {
  return (
    <article className="mx-auto w-full max-w-3xl py-4">
      <h1 className="text-[28px] font-semibold leading-tight [text-wrap:balance]">
        Política de Privacidade
      </h1>
      <p className="mt-2 text-sm text-fg-muted">
        Última atualização: 9 de novembro de 2026
      </p>

      <div className="mt-8 text-base leading-relaxed text-fg">
        <h2 className="mt-8 text-xl font-semibold text-fg">1. Quem somos</h2>
        <p className="mt-2">
          O site <strong>EmpregaNoix</strong> é operado por{" "}
          <strong>André Cauê G.C</strong>, pessoa física, com o objetivo de
          divulgar oportunidades de emprego e facilitar o contato entre
          candidatos e recrutadores/empresas.
        </p>

        <h2 className="mt-8 text-xl font-semibold text-fg">
          2. Quais dados tratamos
        </h2>
        <p className="mt-2">
          Atualmente, o EmpregaNoix{" "}
          <strong>
            não solicita nem coleta dados pessoais de candidatos
          </strong>{" "}
          (não há cadastro, envio de currículo ou formulário de candidatura).
        </p>
        <p className="mt-2">Os dados tratados são:</p>
        <ul className="mt-2 list-disc space-y-1 pl-5">
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

        <h2 className="mt-8 text-xl font-semibold text-fg">
          3. Origem dos dados das vagas
        </h2>
        <p className="mt-2">
          As vagas publicadas no EmpregaNoix são obtidas a partir de grupos públicos
          ou semi-públicos de WhatsApp. Os textos são processados e reescritos
          antes da publicação. Apenas a versão elaborada fica armazenada no
          site. As vagas não são cópia integral das mensagens originais.
        </p>

        <h2 className="mt-8 text-xl font-semibold text-fg">
          4. Finalidade do tratamento
        </h2>
        <p className="mt-2">Os dados são tratados exclusivamente para:</p>
        <ul className="mt-2 list-disc space-y-1 pl-5">
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

        <h2 className="mt-8 text-xl font-semibold text-fg">5. Base legal</h2>
        <p className="mt-2">
          O tratamento dos dados se fundamenta principalmente no{" "}
          <strong>legítimo interesse</strong> (divulgação de oportunidades de
          emprego e funcionamento do site) e, quando aplicável, no
          consentimento (ex.: cookies não essenciais).
        </p>

        <h2 className="mt-8 text-xl font-semibold text-fg">
          6. Compartilhamento de dados
        </h2>
        <ul className="mt-2 list-disc space-y-1 pl-5">
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

        <h2 className="mt-8 text-xl font-semibold text-fg">
          7. Transferência internacional de dados
        </h2>
        <p className="mt-2">
          O site utiliza serviços de infraestrutura localizados fora do Brasil
          (atualmente Vercel e Neon). Dessa forma, dados técnicos de navegação
          e os dados das vagas podem ser processados em servidores localizados
          no exterior. Adotamos medidas para que esse tratamento ocorra de
          forma segura.
        </p>

        <h2 className="mt-8 text-xl font-semibold text-fg">
          8. Cookies e Google Analytics
        </h2>
        <p className="mt-2">
          Caso o Google Analytics seja implementado, utilizaremos cookies e
          tecnologias semelhantes para entender como os visitantes utilizam o
          site. Você poderá gerenciar suas preferências de cookies por meio
          das configurações do seu navegador.
        </p>

        <h2 className="mt-8 text-xl font-semibold text-fg">
          9. Retenção dos dados
        </h2>
        <ul className="mt-2 list-disc space-y-1 pl-5">
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

        <h2 className="mt-8 text-xl font-semibold text-fg">
          10. Direitos do titular
        </h2>
        <p className="mt-2">
          Nos termos da Lei Geral de Proteção de Dados (LGPD), você pode
          solicitar:
        </p>
        <ul className="mt-2 list-disc space-y-1 pl-5">
          <li>Confirmação da existência de tratamento;</li>
          <li>Acesso aos dados;</li>
          <li>Correção de dados incompletos ou desatualizados;</li>
          <li>Eliminação dos dados;</li>
          <li>Portabilidade (quando aplicável);</li>
          <li>Informação sobre compartilhamento;</li>
          <li>Revogação de consentimento;</li>
          <li>Oposição ao tratamento.</li>
        </ul>
        <p className="mt-2">
          Para exercer esses direitos, envie um e-mail para:{" "}
          <strong>empreganoix@outlook.com</strong>
        </p>

        <h2 className="mt-8 text-xl font-semibold text-fg">11. Segurança</h2>
        <p className="mt-2">
          Adotamos medidas técnicas e organizacionais razoáveis para proteger
          os dados contra acessos não autorizados, perda, alteração ou
          qualquer forma de tratamento inadequado.
        </p>

        <h2 className="mt-8 text-xl font-semibold text-fg">
          12. Alterações desta Política
        </h2>
        <p className="mt-2">
          Esta Política de Privacidade poderá ser atualizada periodicamente. A
          versão mais recente estará sempre disponível nesta página, com a
          data da última atualização.
        </p>

        <h2 className="mt-8 text-xl font-semibold text-fg">13. Contato</h2>
        <p className="mt-2">
          Dúvidas sobre esta Política ou sobre o tratamento de dados pessoais
          podem ser enviadas para: <strong>empreganoix@outlook.com</strong>
        </p>

        <div className="mt-12 rounded-md border border-line bg-surface p-4 text-sm leading-relaxed text-fg-muted">
          <p>
            Somos apenas meio de divulgação. As vagas são obtidas de grupos
            públicos de WhatsApp e o contato é disponibilizado após validação
            anti-bot. Não armazenamos dados de candidatura e não nos
            responsabilizamos por interações entre candidatos e empresas.
          </p>
        </div>
      </div>
    </article>
  );
}