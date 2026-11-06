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
                  <a href="/admin/paste" className="hover:text-accent-strong transition-colors">Painel Admin</a>
                </li>
                <li>
                  <a href="/termos-de-uso" className="hover:text-accent-strong transition-colors">Termos de Uso</a>
                </li>
              </ul>
            </nav>
          </div>

          <h2 className="text-3xl font-semibold border-b border-gray-700 pb-4 mb-8">POLÍTICA DE PRIVACIDADE</h2>
        </header>

        <article className="prose lg:prose-xl text-lg leading-relaxed">
          <p>Última atualização: quarta-feira, 4 de novembro de 2026</p>

          <h3>1. Quem somos</h3>
          <p>O site NQU é operado por [Seu Nome Completo], pessoa física, com o objetivo de divulgar oportunidades de emprego e intermediar o contato entre candidatos e empresas.</p>

          <h3>2. Quais dados coletamos</h3>
          <ul className="list-disc pl-5 mb-6">
            <li>Dados fornecidos por candidatos: nome, e-mail, telefone, currículo e informações profissionais que você optar por enviar.</li>
            <li>Dados fornecidos por empresas: informações de contato e descrição da vaga.</li>
            <li>Dados de navegação: endereço IP, tipo de navegador, páginas visitadas e cookies (quando aplicável).</li>
          </ul>

          <h3>3. Finalidade do tratamento</h3>
          <p>Os dados são tratados exclusivamente para:</p>
          <ul className="list-disc pl-5 mb-6">
            <li>Divulgar vagas de emprego;</li>
            <li>Permitir que candidatos se candidatem às vagas;</li>
            <li>Viabilizar o contato entre candidatos e empresas anunciantes;</li>
            <li>Melhorar o funcionamento e a segurança do site;</li>
            <li>Cumprir obrigações legais.</li>
          </ul>

          <h3>4. Base legal</h3>
          <p>Tratamos os dados com base no legítimo interesse, na execução de procedimentos preliminares relacionados a contrato e, quando necessário, no consentimento do titular.</p>

          <h3>5. Compartilhamento</h3>
          <p>Os dados de candidatos são compartilhados apenas com a empresa responsável pela vaga para a qual a candidatura foi enviada. Não vendemos, alugamos ou comercializamos dados pessoais.</p>

          <h3>6. Retenção dos dados</h3>
          <p>
            <strong>Vagas:</strong> expiram e são removidas após 14 dias.<br />
            <strong>Dados de candidatura:</strong> mantidos pelo tempo necessário para a finalidade da intermediação. Após esse período ou mediante solicitação, são excluídos.<br />
            <strong>Dados de navegação:</strong> conforme necessidade técnica e de segurança.
          </p>

          <h3>7. Direitos do titular</h3>
          <p>Você pode solicitar a qualquer momento:</p>
          <ul className="list-disc pl-5 mb-6">
            <li>Confirmação da existência de tratamento;</li>
            <li>Acesso aos dados;</li>
            <li>Correção de dados incompletos ou desatualizados;</li>
            <li>Eliminação dos dados;</li>
            <li>Portabilidade;</li>
            <li>Revogação do consentimento;</li>
            <li>Oposição ao tratamento.</li>
          </ul>
          <p>Para exercer esses direitos, envie e-mail para: suportenqs@outlook.com</p>

          <h3>8. Segurança</h3>
          <p>Adotamos medidas técnicas e organizacionais razoáveis para proteger os dados pessoais contra acessos não autorizados, perda ou alteração indevida.</p>

          <h3>9. Alterações</h3>
          <p>Esta Política pode ser atualizada. A versão mais recente estará sempre disponível nesta página.</p>

          <h3>10. Contato</h3>
          <p>Dúvidas sobre esta Política ou sobre o tratamento de dados pessoais: suportenqs@outlook.com</p>
        </article>
      </div>
    </main>
  );
}