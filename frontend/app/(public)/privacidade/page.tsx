import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Privacidade, Termos e Aviso Legal — NaoQueroUsar",
  description:
    "Saiba como o NaoQueroUsar trata dados pessoais, quais são os termos de uso do board e o aviso de intermediário: somos apenas meio de divulgação de vagas.",
};

export default function PrivacidadePage() {
  return (
    <article className="max-w-[860px]">
      <h1 className="text-[28px] font-semibold leading-[1.2] [text-wrap:balance]">
        Privacidade, Termos e Aviso Legal
      </h1>

      <nav
        aria-label="Índice desta página"
        className="mt-6 rounded-[12px] border border-line bg-surface p-4 text-sm text-fg-muted"
      >
        <ul className="flex flex-col gap-2">
          <li>
            <a href="#privacidade" className="hover:text-accent-soft">
              1. Privacidade
            </a>
          </li>
          <li>
            <a href="#termos" className="hover:text-accent-soft">
              2. Termos de Uso
            </a>
          </li>
          <li>
            <a href="#aviso-intermediario" className="hover:text-accent-soft">
              3. Aviso de Intermediário e LGPD
            </a>
          </li>
        </ul>
      </nav>

      <section
        id="privacidade"
        aria-labelledby="privacidade-heading"
        className="scroll-mt-24"
      >
        <h2
          id="privacidade-heading"
          className="mt-12 text-xl font-semibold leading-[1.2] text-fg"
        >
          1. Privacidade
        </h2>
        <div className="mt-4 flex flex-col gap-4 text-base leading-normal text-fg">
          <p>
            Esta seção descreve, de forma geral, como o NaoQueroUsar lida com
            informações de visitantes e de contatos publicados nas vagas. O
            NaoQueroUsar é um board público de divulgação de vagas e não exige
            cadastro, conta, login ou qualquer etapa de registro para a
            navegação ou para consultar os contatos das vagas publicadas.
          </p>
          <p>
            <strong>Dados que podem ser tratados:</strong> dados técnicos de
            acesso (como endereço IP, tipo de navegador e horário da
            requisição) podem ser registrados de forma automática pelos
            servidores de hospedagem, exclusivamente para segurança, prevenção
            a abusos e diagnóstico técnico. Não criamos perfis de visitantes
            nem utilizamos esses dados para fins de marketing ou
            remarketing.
          </p>
          <p>
            <strong>Contatos publicados nas vagas:</strong> os dados de
            contato (e-mail, telefone, WhatsApp e endereços de perfis ou
            formulários informados por quem anuncia a vaga) são exibidos
            publicamente na página da vaga e tornam-se públicos quando revelados
            pelo visitante. Ao clicar em “mostrar contato”, o visitante assume
            a responsabilidade pelo uso que fizer dessas informações,
            respeitando a legislação aplicável (incluindo a LGPD).
          </p>
          <p>
            <strong>Reportes de vagas:</strong> visitantes podem enviar um
            reporte sobre uma vaga suspeita ou incorreta. Esses reportes podem
            conter um motivo breve e o endereço IP de quem enviou, usados
            exclusivamente para moderação e segurança, sem identificação
            obrigatória e sem criação de perfil.
          </p>
          <p>
            <strong>Armazenamento e retenção:</strong> as vagas publicadas são
            removidas automaticamente aproximadamente 14 dias após a criação.
            Registros de servidor seguem a política de retenção do provedor de
            hospedagem.
          </p>
          <p>
            <strong>Direitos do titular (LGPD):</strong> titulares podem
            solicitar informações, correção ou exclusão de dados pessoais
            tratados por nós. Para isso, ou para qualquer dúvida sobre
            privacidade, entre em contato pelo canal indicado na seção “Aviso
            de Intermediário e LGPD”.
          </p>
          <p>
            <em>
              [Redação jurídica detalhada pendente — sujeito a revisão por
              advogado antes do lançamento. Texto geral e meramente
              informativo.]
            </em>
          </p>
        </div>
      </section>

      <section
        id="termos"
        aria-labelledby="termos-heading"
        className="scroll-mt-24"
      >
        <h2
          id="termos-heading"
          className="mt-10 text-xl font-semibold leading-[1.2] text-fg"
        >
          2. Termos de Uso
        </h2>
        <div className="mt-4 flex flex-col gap-4 text-base leading-normal text-fg">
          <p>
            Ao acessar e utilizar o NaoQueroUsar, você concorda com estes
            Termos de Uso. Se não concordar, não utilize o site. O
            NaoQueroUsar é disponibilizado “como está”, sem garantias de
            disponibilidade, precisão, adequação a um fim específico ou não
            interrupção.
          </p>
          <p>
            <strong>Natureza do serviço:</strong> o NaoQueroUsar é um board de
            divulgação pública de vagas. Não somos empregadora, agência de
            recrutamento, intermediadora de empregos nem garantimos veracidade,
            legalidade, validade ou disponibilidade de qualquer vaga divulgada.
          </p>
          <p>
            <strong>Confidencialidade e adequação:</strong> as vagas são
            curadas manualmente por um único administrador antes da publicação,
            mas isso não constitui verificação completa de verdade, idoneidade
            do empregador, legalidade da vaga, autorização de trabalho ou
            condições de segurança. O visitante é responsável por confirmar
            essas informações antes de se candidatar.
          </p>
          <p>
            <strong>Contatos e candidaturas:</strong> nenhuma candidatura é
            intermediada pelo NaoQueroUsar. Qualquer contato, envio de
            currículo, entrevista ou contratação ocorre diretamente entre
            visitante e anunciante, sem participação do NaoQueroUsar.
          </p>
          <p>
            <strong>Uso permitido:</strong> você não pode utilizar este site
            para spam, extração automatizada de dados (scraping), fraude,
            fraude de identidade, envio de conteúdo ilícito, ou qualquer
            atividade que viole a lei ou os direitos de terceiros. Conteúdo
            ilegal ou suspeito pode ser removido a qualquer momento, sem aviso
            prévio.
          </p>
          <p>
            <strong>Propriedade intelectual e conteúdo:</strong> os textos e o
            design da página pertencem ao NaoQueroUsar. Os conteúdos das vagas
            pertencem a quem os publicou. Nossa marca e design não podem ser
            usados para promover serviços ou vagas sem autorização prévia.
          </p>
          <p>
            <strong>Limitação de responsabilidade:</strong> o NaoQueroUsar não
            se responsabiliza por qualquer dano, perda, prejuízo ou
            frustração decorrente do uso das informações ou contatos exibidos
            no site, nem por ações de empregadores, agências, recrutadores ou
            terceiros.
          </p>
          <p>
            <strong>Alterações destes termos:</strong> estes termos podem ser
            atualizados a qualquer momento. O uso continuado do site após
            alterações representa aceitação das novas condições. A data de
            atualização pode ser indicada no rodapé desta página quando
            aplicável.
          </p>
          <p>
            <em>
              [Redação jurídica detalhada pendente — sujeito a revisão por
              advogado antes do lançamento. Texto geral e
              meramente informativo.]
            </em>
          </p>
        </div>
      </section>

      <section
        id="aviso-intermediario"
        aria-labelledby="aviso-heading"
        className="scroll-mt-24"
      >
        <h2
          id="aviso-heading"
          className="mt-10 text-xl font-semibold leading-[1.2] text-fg"
        >
          3. Aviso de Intermediário e LGPD
        </h2>
        <div className="mt-4 flex flex-col gap-4 text-base leading-normal text-fg">
          <p>
            <strong>Somos apenas meio de divulgação.</strong> O NaoQueroUsar
            não é empregador, agência de recrutamento, intermediador de
            empregos nem representante de qualquer anunciante. Atuamos apenas
            como meio de divulgação e organização pública de informações sobre
            vagas publicadas manualmente após curadoria.
          </p>
          <p>
            <strong>Sem relação contratual:</strong> o uso deste site ou o
            contato com anunciantes não cria vínculo empregatício, societário,
            de representação, de mandato, de parceria, de agência ou de
            qualquer natureza com o NaoQueroUsar. Qualquer contratação,
            promessa, condição de trabalho, remuneração, benefícios ou
            exclusividade é negociada exclusivamente entre visitante e
            anunciante.
          </p>
          <p>
            <strong>Sem garantia de verificação:</strong> aprovação manual de
            uma vaga pelo administrador não significa validação jurídica,
            idoneidade da empresa, legalidade da vaga, registro do
            empregador, correta classificação do cargo ou licitude das
            condições oferecidas. Toda informação exibida é de responsabilidade
            de quem a forneceu.
          </p>
          <p>
            <strong>Responsabilidade do visitante:</strong> antes de se
            candidatar, o visitante deve verificar a idoneidade do anunciante,
            a existência real da vaga, as condições de trabalho e a legalidade
            do processo. Nunca forneça documentos pessoais, senhas, dados
            bancários ou pagamentos a quem solicite; desconfie de vagas com
            promessas de ganhos fáceis, pedido de entrevista sem identificar a
            empresa ou exigência de depósito antecipado.
          </p>
          <p>
            <strong>LGPD (Lei nº 13.709/2018):</strong> o controlador dos
            dados pessoais tratados diretamente em nossa operação (por
            exemplo, dados técnicos de acesso e reportes) responde às
            solicitações de acesso, correção, anonimização, portabilidade e
            exclusão na forma da lei. Dados de contato exibidos nas vagas
            pertencem a quem os publicou, que detém o papel de controlador
            sobre o próprio tratamento. Para exercer direitos ou reportar
            tratamento indevido, utilize o canal de contato abaixo.
          </p>
          <p>
            <strong>Reportes e moderação:</strong> conteúdo suspeito,
            enganoso ou ilegal pode ser removido a qualquer momento, sem aviso
            prévio. O NaoQueroUsar não tem a obrigação de investigar cada
            reporte nem de contatar anunciantes ou visitantes, mas pode
            utilizá-los para aprimorar a moderação.
          </p>
          <p>
            <strong>Contato:</strong> para questões de privacidade, LGPD,
            avisos de conteúdo indevido ou pedidos de remoção, utilize o
            canal de contato indicado no rodapé deste site ou responda pelo
            e-mail oficial informado quando o lançamento for comunicado.
            {" "}
            <em>
              [E-mail de contato para privacidade: pendente — definir endereço
              oficial antes do lançamento.]
            </em>
          </p>
          <p>
            <em>
              [Redação jurídica detalhada pendente — sujeito a revisão por
              advogado antes do lançamento. Texto geral e meramente
              informativo.]
            </em>
          </p>
        </div>
      </section>

      <p className="mt-10 border-t border-line pt-6 text-sm leading-normal text-fg-muted">
        Esta página contém informações gerais. Para questões jurídicas
        específicas, consulte um advogado.
      </p>
    </article>
  );
}
