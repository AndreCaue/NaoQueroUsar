import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Termos de Uso — EmpregaNoix",
  description:
    "Termos de Uso do EmpregaNoix: divulgação de vagas, responsabilidades do usuário, expiração em 14 dias, limitação de responsabilidade e foro de Americana/SP.",
};

export default function TermosDeUsoPage() {
  return (
    <article className="mx-auto w-full max-w-3xl py-4">
      <h1 className="text-[28px] font-semibold leading-tight [text-wrap:balance]">
        Termos de Uso
      </h1>
      <p className="mt-2 text-sm text-fg-muted">
        Última atualização: 9 de novembro de 2026
      </p>

      <div className="mt-8 text-base leading-relaxed text-fg">
        <h2 className="mt-8 text-xl font-semibold text-fg">1. Objeto</h2>
        <p className="mt-2">
          O site <strong>EmpregaNoix</strong> tem como finalidade exclusiva a
          divulgação de oportunidades de emprego e a facilitação do contato
          entre candidatos e recrutadores/empresas. O EmpregaNoix não realiza
          processos seletivos, não intermediaria contratações e não atua como
          agência de emprego.
        </p>
        <p className="mt-4 rounded-md border border-line-strong bg-surface p-4 text-sm leading-relaxed text-fg-muted">
          Somos apenas meio de divulgação de vagas: não realizamos processos
          seletivos, não participamos de contratações e não atuamos como agência
          de emprego.
        </p>

        <h2 className="mt-8 text-xl font-semibold text-fg">
          2. Natureza do serviço
        </h2>
        <p className="mt-2">
          O EmpregaNoix atua apenas como plataforma de divulgação. As vagas publicadas
          são obtidas a partir de grupos públicos ou semi-públicos de
          WhatsApp, sendo processadas e reescritas antes da publicação.
        </p>
        <p className="mt-2">
          Não garantimos a veracidade, atualidade ou legitimidade das vagas,
          nem o resultado de qualquer processo seletivo. O contato com
          recrutadores ou empresas é de inteira responsabilidade do usuário.
        </p>

        <h2 className="mt-8 text-xl font-semibold text-fg">
          3. Uso do site e responsabilidades do usuário
        </h2>
        <ul className="mt-2 list-disc space-y-1 pl-5">
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

        <h2 className="mt-8 text-xl font-semibold text-fg">
          4. Publicação de vagas
        </h2>
        <p className="mt-2">
          As vagas são publicadas exclusivamente pela administração do site.
          Não há, no momento, funcionalidade de publicação de vagas por
          usuários ou empresas.
        </p>
        <p className="mt-2">
          As vagas permanecem disponíveis por 14 dias e são excluídas de forma
          definitiva após esse período.
        </p>

        <h2 className="mt-8 text-xl font-semibold text-fg">
          5. Propriedade intelectual
        </h2>
        <p className="mt-2">
          Todo o conteúdo do site (textos, layout, código, design e demais
          elementos) é de propriedade do EmpregaNoix ou de seus licenciadores. É
          proibida a cópia, reprodução, distribuição ou qualquer forma de uso
          não autorizado.
        </p>

        <h2 className="mt-8 text-xl font-semibold text-fg">
          6. Limitação de responsabilidade
        </h2>
        <p className="mt-2">
          Na máxima extensão permitida pela legislação brasileira, o EmpregaNoix e seu
          operador não se responsabilizam por:
        </p>
        <ul className="mt-2 list-disc space-y-1 pl-5">
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

        <h2 className="mt-8 text-xl font-semibold text-fg">7. Privacidade</h2>
        <p className="mt-2">
          O tratamento de dados pessoais é regido pela nossa{" "}
          <Link
            href="/privacidade"
            className="text-accent-soft underline underline-offset-2 hover:text-accent"
          >
            Política de Privacidade
          </Link>
          .
        </p>

        <h2 className="mt-8 text-xl font-semibold text-fg">8. Alterações</h2>
        <p className="mt-2">
          Estes Termos de Uso podem ser atualizados a qualquer momento. A
          versão mais recente estará sempre disponível nesta página. O uso
          continuado do site após a publicação de alterações implica aceitação
          da nova versão.
        </p>

        <h2 className="mt-8 text-xl font-semibold text-fg">9. Foro</h2>
        <p className="mt-2">
          Fica eleito o foro da comarca de Americana, Estado de São Paulo,
          para dirimir quaisquer controvérsias oriundas destes Termos de Uso,
          com renúncia a qualquer outro, por mais privilegiado que seja.
        </p>

        <h2 className="mt-8 text-xl font-semibold text-fg">10. Contato</h2>
        <p className="mt-2">
          Dúvidas sobre estes Termos de Uso podem ser enviadas para:{" "}
          <strong>empreganoix@outlook.com</strong>
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