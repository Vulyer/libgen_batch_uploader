# -*- coding: utf-8 -*-
#MODULES SECTION#
import zipfile, os, re, hashlib, base64, requests, urllib, hashlib, time, datetime, urllib3, PyPDF2, zlib, lxml
from bs4 import BeautifulSoup
from lxml import etree
from urllib.parse import urlencode, quote_plus
from xml.parsers import expat
#from mobi import Mobi


#GLOBAL VARIABLES#
fhash = None #Hash of the current file, start as None
uncategorized = [] #List of genres not found on the following lists
uncategorized_authors = [] #List of authors not found on the following lists

#Credentials to access LibGen uploaders
user = 'genesis'
passw = 'upload'
credentials = str(base64.b64encode(str(user + ':' + passw).encode("utf-8")), "utf-8")
libgen_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:20.0) Gecko/20100101 Firefox/20.0', \
				'Authorization': str('Basic ' + credentials)}

valid_formats = ['PDF', 'DJVU', 'EPUB', 'MOBI', 'AZW', 'AZW3', 'AZW4', 'FB2', 'RTF', 'DOC', 'DOCX', 'ZIP', 'RAR', 'CBZ', 'CBR', 'CB7']

#Regex lists for genres to decide which collection a book belons to.
fiction = ['.*(A|a)c(c|t)i(ó|o)n ?', '.*(A|a)d?v(a|e)n(t|r)ur(a|e)s?.*', '.*(A|a)mante ?', '.*(A|a)mor *', '.*(A|a)ntolog ?', '.*(B|b)(é|e)lic(a|o) ?', '.*(C|c)ancionero ?', '.*(C|c)h?anto?s?', \
	'.*(C|c)l(a|á|Ã¡)ss?ic(o|a)?s? ?', '.*(C|c)omed(y|ia) ?', '.*(C|c)ontempor(a|á)(nea|ry) ?', '.*(C|c)(ue|o)nt(o|e)s? ?', '.*(D|d)etective ?', '.*(D|d)a?ram(à|á|a)(tic)?a? ?', \
	'.*(D|d)(i|y)stop(í|i)a ?', '.*(E|e)r(ò|o|ó|Ã³)s?t?i?c?(sm)?(o|a|) ?', '.*(F|f)anfic ?', '.*(F|f)ant(a|á)s(tic|y|í|i)(o|a)? ?', '.*(F|f)ic(c|t)i(o|ó|ò)n ?', \
	'.*(G|g)ui(o|ó|Ã³)n ?', '.*(H|h)orror ?', '.*(H|h)umou?r ?', '.*(I|i)nfantil? ?', '.*(I|i)ntr?(i|í)gu?(a|e) ?', '.*(J|j)uvenil ?', '.*(M|m)ister(io|y) ?', \
	'.*(N|n)arr?a(t|c)i(v(a|e)|o|ó)n? ?', '.*(N|n)oir ?', '.*(N|n)ou?vel(k?a)? ?', '.*(P|p)as+i(o|ó)n ?', '.*(P|p)o(e|é)?(try|(s(i|i|Ã\xad)a)|mas?|tica?s?) ?', \
	'.*(P|p)olic(í|i)a(c(o|a)|l) ?', '.*(P|p)ros(a|e) ?', '.*(P|p)ulp ?', '.*(R|r)?o(m|n)(à|á|a)n(tica?)?(ism(o|ta))? ?', '.*(R|r)ealis ?', '.*(R|r)elato ?', '.*(R|r)ol ?',\
	'.*(S|s)atírica ?', '.*(S|s)erie ?', '.*(S|s)oneto?s? ?', '(L|l)itera(tu)?r(a|e|y)? ?', '.*(S|s)uspens ?', '.*(T|t)eatro ?', '.*(T|t)error ?', '.*(T|t)hriller ?', '.*(T|t)hriller ?', '.*(T|t)raged(ia|y) ?', \
	'.*(T|t)rilog ?', '.*FIC(T|C)I(O|Ó)N ?', '.*JUVENILE? ?', '.*NOVELA? ?', '.*POETRY ?', '.*_history', '.*libro Elige tu destino ?', '.*miedo ?', '.*(O|o)t(he)?ro?s', 'Gay', \
	'(C|c)onspiraci(o|ó)n', '(C|c)ontempor(áne|ary)', '(C|c)r(i|í)me(nes)?', '(E|É|e|é)pic', '(F|f)(a|á|Ã¡)bulas?', '.*(H|h)ist(ò|o|ó)(r|t)ic(a|o)', '(LCO|POE|FIC)\\d{6}', \
	'(M|m)(i|y)th?olog(ia|ía|y)', '(N|n)arraciones ?', '(N|n)egra', '(P|p)aranormal', '(P|p)icaresque', '(P|p)oe(s(í|i)a|try) ?', '(P|p)rehistoria', '(S|s)(á|a|Ã¡)tir(a|e)', \
	'(S|s)entimental', '(S|s)tor(y|ies) ?', '(S|s)urrealismo?', '(T|t)r?h?iller', '.*(V|v)amp(i|y)r(o|e)?s? ?', '(V|v)ariada', 'ASSAIG', 'AVENTURAS', 'Assaig', 'BÃ©lica', 'CF', \
	'CIENCIA FICCION', 'CIENCIA FICCIÓN', 'CIFI', 'CLASICO GRIEGO', 'CONTEMPORANEA', 'Chick?( |-)lit', "Children's Books", 'Cinematografía', ' ?(C|c)ostum(br)?is(ta|mo) ?', 'Thistledown ?', \
	'EROTICA', 'OTROS', 'Eleberria', 'English', 'Erzählung ?', 'Erótiva', 'Eslava', 'Espionaje', 'Eótica', 'FANTASIA', 'Fansatia', '.*(F|f)(a|á)bu?l(a|e)s? ?', 'Giallo', 'HUMOR', 'Ingl(e|é|Ã©)s', \
	'Introspectiva', 'Juv', 'Lez', 'MISTERIO', 'NARRATIVA ?', 'NaRRAtiva ?', 'NaRRativa ?', 'Naarativa', 'NarraTIVA ?' 'Narraqtiva', ' ?Leibowitz ?', 'castellano', 'Montalbano', \
	'Narrazioak', 'Narrrativa', 'Navidad', 'Norrativa Variada', 'Nrrativa', 'Odinokij Volk', 'Otros idiomas', 'POEMAS', 'Polar', 'Polard', 'Polic', 'Precuela', 'ROMANTICA', 'ROMANTICA CONTEMPORANEA', \
	'Realto', 'Romanzo Giallo', 'RomÃ\xa0n', 'Romántca', 'S2', 'SF', 'Saga ?', 'Saiakera', 'Scifi', 'Star Wars ?(C|c)l(a|á)s+ic(os|a)l? ?', 'Surrealismo', 'TEATRO', 'TEATRO CLASICO', 'TERROR', 'Teatr ?', \
	'Teen & Young Adult', 'UCRONÍA', 'adv_ ?', 'ahistórica', 'cf', 'child', 'cifi', 'contemporanea', 'det_', 'dramaturgy', 'ebook', '(E|e)?(S|s)p(i|í|y)(o|a)(na(j|g)e)?s?', 'f_history', 'fic', 'gótico', 'lit', \
	'love', 'mystery', 'nARRATIV ?', 'nOVELA ?', 'narra', 'novel·la negra', 'otros idiomas frances', 'polar', 'prosa contemporanea', 'prose', 'Sherlock Holmes', 'Kementxu', 'OhCaN', 'Oeste', 'Tramórea', \
	'racconto giallo', 'saiakera', 'sci-fi', 'sexo', 'sf', 'space_opera', 'steampunk', 'superheroes', 'surrealismo', 'thri', 'ucron', '.*(H|h)aikus? ?', 'Premio UPC', 'Col\.?(ecci(o|ó)n)? N(OVA|ova) ', 'Ganadores', 'Premio ?']

non_fiction = ['.*(A|a)lgorith?mo?s? ?', '.*((A|a)nti)?(P|p)?s(i|y)(qu|ch)iatr(ía|ia|y) ?', '.*((A|a)uto)?(B|b)iogr(a|á)(f|ph)(i|í|y)c?(a|e|o)?s? ?', '.*((C|c)onflicto?s?| |(I|i)nterna(c|t)ional){2} ?', \
	'.*((C|c)|(Q|q))u(a|á)nt ?', '.*((F|f)(ranc|ree))?(M|m)ason(ería|ry) ?', '.*(T|t)h?eor(ia|ía|y|ema?s?) ?', '.*((I|i)n)?(S|s)eguridad ?', '.*((M|m)eta)?(F|f|P|p)h?(i|í|y)sic(a|s) ?', \
	'.*(A|a)bla(c|t)i(ó|o)n ?', '.*(A|a)cad(e|é)mic ?', '.*(A|a)diestramiento ?', '.*(A|a)dministra(c|t)i(o|ó)n ?', '.*(A|a)jedrez ?', '.*(A|a)lquimia', '.*(A|a)n(á|a)l(i|y)sis ?', \
	'.*(A|a)narquismo ?', '.*(A|a)natomia ?', '.*(A|a)necdotario ?', '.*(A|a)ngeolog(ia|ía|y) ?', '.*(A|a)nth?ropolog(y|(í|i)(a|e)) ?', '.*(A|a)r(qui|chi)tectur(a|e) ?', \
	'.*(A|a)r(qu|ch(a|ä)?)(e|é)olog(y|(í|i)(a|e)) ?BUSINESS', ' (A|a)rte?s? ?', '.*(A|a)strolog ?', '.*((A|a)stro)?(N|n)(a|á)utica?s? ?', \
	'.*(A|a)th?eismo? ?', '.*(A|a)utibiografía ?', '.*(A|a)utoayuda ?', '.*(A|a)utoconocimiento ?', '.*(B|b)ases? de (D|d)atos ? ?(F|f)isiopatologia ?', '.*(B|b)ienestar ?', \
	'.*(B|b)iolog.*', '.*(B|b)romatolog ?', '.*(B|b)rujer(í|i)a ? ?(F|f)inan(zas|ces) ?', '.*(B|b)usiness ?', '.*(C|c)(a|á)tedras? ?', \
	'.*(C|c)(o|ó)d(ex|ice) ?', '.*(C|c)apitalismo ?', '.*(C|c)artas ?', '.*(C|c)at(a|á)log(o|ue) ?', '.*(C|c)ath?olicismo? ?', '.*(C|c)h?ardiogra(fia|fía|phy) ?', \
	'.*(C|c)h?ristianismo? ?', '.*(C|c)hamanismo ?', '.*(C|c)hemi(cal|stry) ?', '.*(C|c)hess ?', '.*(S|s)?(C|c)i(e|é)n(cia|sce|t(í|i)fi(que|c)o?)s? ?', '.*(C|c)ine ?', \
	'.*(C|c)ocina ?', '.*(C|c)om+unica(c|t)i(o|ó)n ?', '.*(C|c)omput ?', '.*(C|c)omunicación ?', '.*(C|c)omunicación ?', '.*(C|c)onferenc(ia|e) ?', '.*(C|c)onstitu(t|c)i(o|ó)n ?', \
	'.*(C|c)ontabilidad ?', '.*(C|c)ook(ing)* ?', '.*(C|c)orrupción ?', '.*(C|c)r(i|í)ti(ca|cism|que) ?', '.*(C|c)rianza ?', '.*(C|c)h?r(ó|o)ni(ca|cles|que) ?', \
	'.*(C|c)ultur(a|e)l? ?', '.*(C|c)uración ?', '.*(C|c)urso ?', '.*(D|d)atabases? ?', '.*(D|d)ecoraci(o|ó)n ?', '.*(D|d)emocrac(ia|y) ?', '.*(D|d)eportes? ?', '.*(D|d)erecho ?', \
	'.*(D|d)erecho ?', '.*(D|d)esarroll ?', '.*(D|d)ial(e|é)ctica?s? ?', '.*(D|d)iar(i|y)o?e?s? ?', '.*(D|d)ic(t|c)ionar(io|y) ?', '.*(D|d)idáctic(o|a)s? ?', \
	'.*(D|d)iet((e|é)tic)?a?', '.*(D|d)iscurso ?', '.*(D|d)iseño ?', '.*(D|d)ib?v?ulga(c|t)i(o|ó)n ?', '.*(D|d)ocen ?', '.*(D|d)ocument ?', '.*(E|e)*(S|s)pirit ?', \
	'.*(E|e)?(S|s)tud(io|y|ie)s? ?', '.*(E|e)?strateg(y|ia) ?', '.*(E|e)clesiología ?', '.*(E|e)colog(ia|ía|y) ?', '.*(E|e)conom(ía|ia|y) ?', '.*(E|e)duca(c|t)i(ó|o)n ?', \
	'.*(E|e)femérides', '.*(E|e)lectr(o|ó)(nic)?a?s? ?', '.*(E|e)mbriolog(ia|ía|y) ?', '.*(E|e)mpiri(ci)?sm ?', '.*(E|e)mprendimiento ?', '.*(E|e)mpresa ?', \
	'.*(E|e)nfermedad ?', '.*(E|e)ngineering ?', '.*(E|e)nsayo ?', '.*(E|e)nseñanza ?', '.*(E|e)ntrevista ?', '.*(E|e)pistemolog(y|ía|ia) ?', '.*(E|e)scritos ?', '.*(E|e)soterismo? ?', \
	'.*(E|e)spiritual ?', '.*(E|e)ssay ?', '.*(E|e)sta(d|t)(i|í)stica?s? ?', '.*(E|e)tnolog ?', '.*(E|e)tolog(ia|ía|y) ?', '.*(E|e)x(e|é)gesis ?', '.*(E|e)xplicaci(o|ó)n ?', \
	'.*(F|f)amilia ?', '.*(F|f)ascismo? ?', '.*(F|f)eminismo? ?', '.*(F|f)ertili(ty|dad) ?', '.*(F|f|Ph|ph)iloso(f|ph)(ía|ia|y) ?', '.*(F|f|Ph|ph)(i|y)siolog(ia|ia|y) ?', '.*(F|f)olklore ?', '.*(F|f)orens(e|ic)s? ?', \
	'.*(F|f)otograf(i|í)a ?', '.*(F|f)undamentos ?', '.*(G|g)?(A|a)stronom(i|í|y)(a|c)? ?', '.*(G|g)ender ?', '.*(G|g)eneal(o|ó)g ?', '.*(G|g)enética', '.*(G|g)eogra ?', \
	'.*(G|g)eometr(y|ia|ía) ?', '.*(G|g)grammar ?', '.*(G|g)rammar', '.*(G|g)u(í|i)a ?', '.*(G|g)uide ?', '.*(G|g)énero ?', '.*(H|h)ealth ?', '.*(H|h)er(á|a)ldica? ?', '.*(A|a)ntropología ?', \
	'.*(H|h)ermen(e|é)uth?ica?s?', '.*(P|p)roductividad', '.*(H|h)ist(o|ò|Ã²|Ã³)i?ri?(a|y)?(ci)?(ty|dad)? ?', '.*(H|h)olocausto ?', '.*(H|h)umanidad?es ?', \
	'.*(I|i)glesia ?', '.*(I|i)luminación ?', '.*(I|i)mperialismo ?', '.*(I|i)mpuestos? ?', '.*(I|i)nform ?', '.*(I|i)ngenier(í|i)a', '.*(I|i)nstitu(c|t)i(o|ó)ne?s? ?', '.*(I|i)nstruc(c|t)i(o|ó)ne?s? ?', '.*(I|i)ntroduc(c|t)i(o|ó)n ?', \
	'.*(I|i)nvectiva ?', '.*(I|i)nvestiga(c|t)i(o|ó)n ?', '.*(I|i)slam ?', '.*(J|j)ardin ?', '.*(J|j)ehova ?', '.*(J|j)udicial ?', '.*(J|j)ur(i|í)dica ?', '.*(L|l)(o|ó)gica? ?', \
	'.*(L|l)acan ?CRIM-UNAM', '.*(L|l)(a|e)ngua(g|j)e ?', '.*(L|l)aw ?', '.*(L|l)ecciones ?', '.*(L|l)egislación ? ?TRAVAIL ?', '.*(L|l)iderazgo ?', '.*(L|l)ingu(i|í)stic(a|o)?s? ?', \
	'.*(L|l)iterar ?', '.*(L|l)iterary ?', '.*(L|l)uminotecnia ?', '.*(M|m)(e|é)th?odo?(s|log)(ia|ía|y|ie)?s? ?', '.*(M|m)(u|ú)sica? ?', '.*(M|m)anagement ?', \
	'.*(M|m)anual ?', '.*(M|m)arketing ?', '.*(M|m)arxismo?', '.*(M|m)ath*em(a|á)th*ic(a|s) ?', '.*(M|m)ath?em(a|á|Ã¡)tica?s? ?', '.*(M|m)edic(in(a|e))? ?', \
	'.*(M|m)edicina ?', '.*(M|m)emo(rias|irs) ?', '.*(M|m)indfulness ?', '.*(M|m)odel(ing|ado) ?sindrome izquierdoso', '.*(M|m)ormon ?', '.*(M|m)ística?s? ?', '.*(M|m|P|p)atrimonio ?', \
	'.*(N|n)atural ? ?(M|m)editaci(o|ó)n ?', '.*(N|n)ature ?', '.*(N|n)azismo ?', '.*(N|n)on? (F|f)ic(c|t)i(o|ó)n ?', '.*(O|o)ratoria ?', '.*(O|o)rganiza(c|t)i(o|ó)ne?s? ?', \
	'.*(O|o)rienta(c|t|l)i(sm)?(o|ó)?n?', '.*(C|c)ongres+o? ?', '.*(O|o)rth?og(e|é)nesis ?', '.*(O|o)rth?oped(ia|y) ?', '.*(O|o)rtograf(ía|ia|y) ?', '.*(P|p)?(S|s)(y|i)ch?olog(ia|ía|y) ?', \
	'.*(P|p)anader(i|í)a ?', '.*(P|p)apiroflexia ?', '.*(P|p)edagogia ?', '.*(P|p)edagogía ?', '.*(P|p)ensamiento ?', '.*(P|p)eriodismo ?', '.*(P|p)eriodismo ?', '.*(P|p)eronismo? ?', \
	'.*(P|p)ol(i|í)tica?s? ?', '.*(P|p)reguntas y (R|r)espuestas ?', '.*(P|p)rocedimientos ?', '.*(P|p)rogram(aci(o|ó)n|ming) ?', '.*(R|r)?(E|e)volu(t|c)i(o|ó)n ?', '.*(S|s)(i|y)stema?s? ?'\
	'.*(P|p)s(i|y)ch?oan(a|á)l(i|y)sis ?', '.*(P|p)s(i|y)ch?olog(ía|ia|y) ?', '.*(P|p)sicomot ?', '.*(P|p)ublicidad ?', '.*(P|p)ython ?', '.*(P|p|F|f)h?iloso(fía|phy) ?', \
	'.*(Q|q)u(i|í)mica ?', '.*(R|r)eceta ?', '.*(R|r)elaciones ?', '.*(R|r)eligi(ó|o)(n|so) ?', '.*(R|r)eportajes ?', '.*(R|r)esearch ?', '.*(S|s)(i|y)mbolog(ia|ía|y) ?', '.*(S|s)alud ?', \
	'.*(S|s)atanism ?', '.*(S|s)cience ?', '.*(S|s)ecurity ?', '.*(S|s)eminar ?', '.*(S|s)emi(o|ó)tic(a|o)?s? ?', '.*(S|s)exolog(ia|ía|y) ?', '.*(S|s)exuali(dad|ty) ?', \
	'.*(S|s)iglos? [A-Z]{1,} ?', '.*(S|s)ocial ?', '.*(S|s)ociales ?', '.*(S|s)ocialismo ?', '.*(S|s)ocie(dad|ty) ?', '.*(S|s)ociolog(ía|ia|ie|y) ?', '.*(S|s)oftware ?', \
	'.*(S|s)ufismo? ?', '.*(T|t)axonomía ?', '.*(T|t)ecnología ?', '(T|t)(e|é)ch?ni(co|ca|que)(s|l)? ?', '.*(T|t)h?eolog(ía|ia|ie|y) ?', '.*(T|t)h?erap(euta|y|ia|ie)s? ?', '.*(T|t)ranscrip(c|t)i(o|ó)n ?', '.*(T|t)ravel ?', \
	'.*(U|u)niversi ?', '.*(V|v)arios ?', '.*(V|v)eterinar ?', '.*(V|v)iat?(j|g)es ?', '.*(É|é|E|e)th?ica?s?', '.*ADMINISTRACION ?', '.*ANALISIS ?', '.*ANTH?ROPOLOG(I|Y)(A|E) ?', \
	'.*ARCHEOLOGIE ?', '.*Aborígenes ?', '.*Adolescence ?', '.*Body ?', '.*Brasil ?', '.*CEPAL ?', '.*CRITIC(A|ISM) ?', '.*(C|c)inematogra(f|ph)(ía|ia|ie|y) ?', '.*Cr(ò|o|ó)nica ?', \
	'.*DIRECCION DE PROYECTOS ?', '.*Diez Mandamientos ?', '.*ECONOMICO ?', '.*EDUCA(T|C)ION ?', '.*EMPLEO ?', '.*Edad del Hierro ?', '.*Educar ?', '.*España ?', '.*Estudio ?', \
	'.*FEMINISMO? ?', '.*FLACSO ?', '.*Family & Relationships ?', '.*GENERO ?', '.*GNU/Linux ?', '.*GRAMÁTICA ?', '.*GRUPOS ETNICOS ?', '.*HISTOIRE ?', '.*HISTORIOGRAFÍA ?', \
	'.*IDEOLOGIAS ?', '.*(I|i)deolog(ia|ía|y|ie) ?', '.*Life Stages ?', '.*MEDIC ?', '.*MEDIO AMBIENTE ?', '.*Mind ?', '.*México ?', '.*Obras económicas ?', '.*Ocultismo ?', '.*POLITIC ?', '.*PREVENCIÓN ?', \
	'.*PSICOLOGIA ?', '.*Parenting ?', '.*Perú ?', '.*SCIENCE ?', '.*SCIENCES? ?', '.*SOCIAL ? ?(S|s)ocial ?', '.*Self-Help ?', '.*Sociedad ?', '.*TESIS ?', '.*Teaching ?', \
	'.*archive.org ?', '.*booksmedicos.org', '.*catequistas ?', '.*decolonizacion ?', '.*derecho comunitario ?', '.*enseñanza ?', '.*ethnic ?', '.*musulman ?', '.*nonfiction ?', \
	'.*patológico ?', '.*programacion ?', '(A|a)ctuali(dad|ty)', '(B|b)ot(a|á)nica', '(C|c)onocimientos? ?', '(C|c)ursos? ((D|d)e)? ?', '(D|d)iagn(o|ó)stico?s*', \
	'(D|d)ic(c|t)ionar(y|io)', '(D|d)iscipl ?', '(D|d)ivorc(io|e)', '(E|e)nc(i|y)clopedia', '(E|e)nsayo', '(G|g)esti(o|ó)n', '(H|h)istorico', '(H|h)ogar', '(I|i)ndependentismo?', \
	'(L|l)(e|a)ngua(j|g)e', '(M|m)agi(a|c) ?', '(M|m)asoner(ía|ia)', '(P|p)ediatría', '(P|p)ensamiento', '(P|p)hilo ?', '(R|r)eligion', '(R|r)emedio ?', '(S|s)em(a|á)ntic(a|s) ?', \
	'(S|s)ubgéneros', '(TEC|HIS|SCI|LIT|LAN|MED|SOC|PHI|BUS)\\d{6}', '(T|t)(é|e)ch?nic(os?|al) ?', '(T|t)antra', '(T|t)estigos de Jehová', '(T|t)estimonio', '(T|t)ransdisciplina', \
	'(T|t)re?at(a(miento|do)|y) ?', '(T|t)raumatolog(ia|ía|y) ?', '(Y|y)oga', 'ALADAA', 'Adobe Acrobat', '.*(A|a)natom(ía|ia|y) ?', 'Apologética', 'Aprendizaje', 'Armauirumque', 'Aspectos de la Misericordia ?', \
	'Auto-ajuda', 'BIENESTAR', 'BIOGRAFIA', 'BOOKSMEDICOS.ORG', 'Biagrafía', 'Bible', 'Biblioteca Virtual IFC', 'BiorafÃ\xada', 'Biorafía', 'Budismo', 'CFF', 'COCINA', 'COCINA - ANJI', \
	'CRIM-UNAM ?', 'Chamanismo', 'Composition', 'Conjuras', 'Creative Writing', 'Cuba', 'DEMOCRACIA', 'Divulgaci', 'ECONOMICS ?', 'Epistolar', 'Este  ? libro', 'Eurasia', \
	'F(I|Í|Ã\x8d)SICA', 'FAES, mercado trasatlántico ?', 'FCE', 'FILOSOFÍA', 'FOMIX-CIDYT;', 'GEOGRAPHIE', 'GRAN ORIENTE DE FRANCIA LAICISMO, DEISMO Y ATEISMO Español', 'General', \
	'Gnosis', 'HBAH', 'HISTO(RY|OIRE|RIA) ?', 'HISTORIA ?', 'Hacker', 'Hechicería', 'Hidrología de Superficie', 'Hinduismo', 'Historical & Comparative', 'História', 'Histórico-Político', \
	'Hist�rico-Pol�tico', 'INVESTIGACI(Ã“|O|Ó)N', 'INVESTIGACIÓN', 'Idiomas', 'Institución Fernando el Católico', 'Inteligencia', 'Internet', 'Java', 'Juventud', 'LANGUAGE ARTS & DISCIPLINES', \
	'MANUAL', 'Memoria', 'Memorias', 'Memòries', 'Misc', 'No Ficción', 'No ficciÃ³n', '.*(O|o)cult(o|ism)o?s? ?', 'Océano Índico,', 'Orwell', 'PRODUCTIVIDAD CIBERNÉTICA', 'PediatrÃ\xada', \
	'Peligros y consecuencias', 'Psychopathology', 'Public Relations', 'RELIGIÓN', 'REVOLUCIÓN', 'Referencia', 'Referencia', 'SISTEMA PENAL', 'SQL Sistemas', 'Science', \
	'Segunda Guerra Mundial', 'Self-Help', 'Self-Improvement', 'Sexo', 'Sociedades Secretas', 'Vaarios', 'Visual Basic 6', '.*(E|e)dad ?', '.*(M|m)igra(c|t)i(o|ó)ne?s? ?', \
	'alumnos', 'amor', 'annales', 'antique', 'antropologÃ\xada', 'armonía', 'assaig', 'biogr_leaders', 'biologÃ\xada', 'biz_', 'bocadillos', 'búsqueda', 'casos', 'comp_www', \
	'conciencia emocional', 'dIVULGACION', 'dibvulgaciÃ³n', 'dibvulgación', 'diosestinta.blogspot.com', 'energía', 'health_psy', 'histor_military', 'home',  '.*(B|b)ases? de (D|d)atos? '\
	'http://bookmedico.blogspot.com', 'http://letrae\\.iespana\\.es', 'innovacion', 'matemÃ¡ticas', 'nonf', 'oración', 'periodic ?', 'plenitud', 'predicación', 'programacio19 on ?', \
	'protecciónPresentación', 'redes sociales', 'ref', 'refugiados', 'relaciones', 'religiÃ³n', 'sacramento', 'santidad', 'sci', 'sesiones de la CEPAL', 'socio-ambiente', \
	'superación personal', 'transgeneracional', 'trrading', 'trrading', 'vision cuántica', 'vitalidad', 'www.DecidaTriunfar.net', 'www.FreeLibros.(me|org|com)', 'www.psikolibro.tk', \
	'.*(A|a|Á|á)lgebra ?', '.*(M|m)etabolismo? ?', '.*(G|g)eolog(ia|ía|y|ie) ?', '.*(G|g)imnas(ia|tics) ?', '.*(G|g)los+ar(y|io) ?', ' ?(C|c)ocktails ?', '.*(N|n)utri(c|t)i(o|ó)n ?', \
	'(A|a)limentaci(ó|o)n', '(P|p)a(n|m)(f|ph)leto?s? ?', '.*(C|c)(o|ó)d(ex|igo|ing) ?', 'GusiX', '(T|t)ao', '.*(M|m)edi(a|á)(tic)?(o|a)? ?', '.*(T|t)oleranci?(a|e) ?', 'Conquista Española']

comics = '.*(C|c)(o|ó)mics?.*', '.*(M|m)anga.*'

#Regex lists for authors to decide which collection a book belongs to.
authors_fic = ['(J|R|R|\.|,| |Tolkien){3,}', '(Franz|,| |Kafka){3,}', '(Sophie|,| |Pembroke){3,}', '(Agnew|,| |Denise){3,}', '(Clancy|,| |Tom){3,}', \
				'(Pedro|,| |Antonio|de|Alarcón){3,}', '(Daniel|,| |Alibert-Kouraguine){2}', '(Marqués|,| |Marquis|de|Sade){3,}', '(Carlos|,| |Ruiz|Zafón){4,}', \
				'(Alexander|,| |S\.|Pushkin){5,}', '(Fernando|,| |Pessoa){3,}', '(LOPE|,| |DE|VEGA){3,}', '(Pedro|,| |Calderón|de la Barca){3,}', \
				'(Charlotte|,| |Brontë){3,}','(Breton|,| |De|Los|Herreros|Manuel){4,}', '(Lester|,| |Ray){3,4}', '(Delorbe|,| |Karen){3,4}', '(Dessen|,| |Sarah){3,4}', \
				'(Disney|,| |Walt){3,4}', '(Albarracin|,| |Gemma){3,4}', '(Calvo|,| |Poyato|Jose){4,}', '(Lugones|,| |Leopoldo){3,4}', '(Alarcon|,| |Pedro|Antonio|de){7,}', \
				'(Smirnov|,| |Lara){3,4}', '(Smith|,| |Wilbur){3,4}', '(Somoza|,| |Ramon){3,4}', '(Steel|,|,| |Danielle){3,4}', '(Stephen|,| |King|Susan){3,4}', '(Stephenson|,| |Neal){3,4}', \
				'(Stilton|,| |Geronimo){3,4}', '(Stoker|,| |Bram){3,4}', '(Jodorowsky|,| |Alejandro){3,4}', '(Jimenez|,| |Lozano|Jose){5,6}', \
				'(Jaramillo|,| |Levi|Enrique){5,6}', '(Altolaguirre|,| |Manuel){3,}','(Ana|,| |Alcolea){3,}', '(Sara| |Isabel|,|Acosta| |López){7,}', \
				'(Aaron|,| |Tiffany){3,}', '(Andrews|,| |Ilona){3,}', '(Rub(e|é)n|,| |Dar(i|í)o){3,}']

authors_non = ['(Gadamer|,| |Hans|Georg){3,}', '(Robert|,| |Kiyosaki){3,}', '(Arsuaga|,| |Juan|Luis){3,}', '(Michel|,| |Foucault){3,}', \
				'(Arthur|,| |Schopenhauer){3,}', '(Rousseau|,| |Jacques|Jean){3,}', '(Bobbio|,| |Norberto){3,}', '(Jacques|,| |Lacan){3,4}', '(Adorno|,|,| |Theodor){3,4}', \
				'(Agamben|,| |Giorgio){3,4}', '(Fidel|,| |Alejandro|Castro|Ruz){4,}', '(Georges|,| |Dumezil){3,}', 'Instituto Cultural Quetzalcoatl', \
				'(Adobe|,| |Systems|Incorporated){3,}', '(Armando|,| |Aguilar|Márquez){3,}', '(Miguel|,| |y|Nicolás|Wiñazki){3,}', \
				'(Centro|,| |Carismatico|Minuto|de|Dios){3,}', '(Jean|,| |Paul|Sartre){3,}', '(Raúl|,| |Scalabrini|Ortiz){3,}', '(Dale|,| |H|Schunk){3,}', \
				'(Diego|,| |Schurman){3,}', '(Scott|,| |Pretorius){3,}', '(Panasonic|,| |Communications|Co|Ltd){3,}', '(León|,| |Rozitchner){3,}', \
				'(Alessandro|,| |Roncaglia){3,}', '(Kim|,| |Potowski){3,}', '(Piaget|,| |Jean){3,}', '(Ortega|,| |Gasset|José){3,}', '(Rodolfo|,| |Mondolfo){3,}', \
				'(Centro|,| |Malik|Fahd|para|la|impresión|del|Sagrado|Corán){5,}', '(Göyrgy|,| |Lukacs){3,}', '(JOHN|,| |LOCKE){3,}', '(Psicoanálisis|,| |Radiofonía|Televisión){3,}', \
				'(Julia|,| |Kristeva){3,}', '(Saul|,| |Kripke){3,}', '(KOLAKOWSKI|,| |Leszek){3,}', '(Martin|,| |Heidegger){3,}', '(José|,| |Pablo|Feinmann){4,}', \
				'EZLN', '(Di|,| |Bernardo|Giuliano){4,}', '(Tomás|,| |Bulat){3,}', '(BJA|,| |Biblioteca|Jurídica|Argentina){3,}', \
				'(Roland|,| |Barthes){3,}', '(Jose|,| |Enrique|Amaro|Soriano){3,}', '(Slavoj|,| |(Z|Ž)i(z|ž)ek){3,}', '(Karl|,| |Weintraub){3,}', '.*Ministerio.*', \
				'(CIDE|,| |Centro|Investigación|Documentación|Educativa){3,}', '(Stevenson|,| |David){3,}', '(James|,| |Alinder){3,}',\
				'(Eduardo|,| |Soto|Pineda){3,}', '(Bernardo|,| |Sorj){3,}', '(Thomas|,| |Jean|Umiker|Sebeok){3,}', '(Aguaviva|,| |Claudio){3,}', \
				'(Fray|,| |Bartolomé|de|las|Casas){3,}', '(Giorgio|,| |Colli){3,}', '(Durkheim|,| |Emilio|David|(E|É)mile){3,}', '(Binford|,| |Lewis){3,4}', \
				'(Allen|,| |Steve){3,4}', '(Aleister|,| |Crowley){3,4}', '(Carl|,| |Sagan){3,4}', '(Tizon|Garcia|,| |Jorge){3,4}', '(Eugenio|,| |Zaffaroni){3,}', 
				'(Alonso|,| |Schokel|Luis){4,}', 'Varios', '(Aivanhov|,| |Omraam|Mikhael){3,4}', '(Aldazabal|,| |Jose){3,4}', '(Sloterdijk|,| |Peter){3,4}'\
				'(Soler|,| |Colette){3,4}', '(Stallman|,| |Richard){3,4}', '(Stalin|,| |Jose|Iosif|Joseph){3,4}', '(Stamateas|,| |Alejandra|Bernardo){3,4}', \
				'(Stanislavski|,| |Konstantin){3,4}', '(Starobinski|,| |Jean){3,4}', '(Steiner|,| |George){3,4}', '(Stephen|,| |Hawking){3,4}', \
				'Susaeta', '(Zweig|,| |Stefan){3,4}', '(Beuchot|,| |Mauricio){3,4}', '(Besant|,| |Annie){3,4}', 'Jenofonte', '(Jauretche|,| |Arturo){3,4}', \
				'(Jaspers|,| |Karl){3,4}', '(Bruce| |Ackerman){3,}', '(Aguaviva|,| |Claudio.){3,}', '(Ismael|,|Aguayo| |Figueroa){4,}', \
				'(Clodomiro| |Almeyda){3,}', '(Servicio| |Editorial|de|la|Universidad|del|País|Vasco){14,}', '(José| |Altshuler){3,}', \
				'(Claudi| |Alsina){3,}', '(Luis| |Álvarez|,|Colín){3,}', '(Aldo| |Lavagnini){3,}', '(Alvarado| |Ortiz|,|Carlos){5,}', '(Karl|,| |Marx){3,}', \
				'(Eric| |J|,|Hobsbawm){3,}', '(Ortega| |y|Gasset|,|José){7,}', '(Piaget|,| |Jean){3,}', '(Viera|,| |Javier| |Ramirez){5,}', \
				'(Alexievich|,| |Svetlana){3,}', '(Avrich|,| |Paul){3,}', '(Georges|,| |Bataille){3,}', '(Blumemberg|,| |Hans){3,}', '(Bueno|,| |Gustavo){3,}', \
				'(Burke|,| |Peter){3,}', '(Camus|,| |Albert){3,}', '(George?|, |Wilhelm|Friedrich|Hegel){4,}', '(Vattimo|,| |Gianni){3,}', '(John|,| |Locke){3,}']


#METADATA FUNCTIONS#

def get_metadata(fname): #Main metadata function. Calls the appropiate function to get metadata according to filetype
	if ".fb2" in fname or ".FB2" in fname:
		metadata = get_fb2_info(fname)
		metadata['extension'] = '.fb2'
	elif ".epub" in fname or ".EPUB" in fname:
		metadata = get_epub_info(fname)
		try: metadata['extension'] = '.epub'
		except TypeError: return metadata
	elif ".pdf" in fname or ".PDF" in fname:
		metadata = get_pdf_info(fname)
		try: metadata['extension'] = '.epub'
		except TypeError: return metadata
	elif ".mobi" in fname or ".MOBI" in fname:
		metadata = get_mobi_info(fname)
		try: metadata['extension'] = '.mobi'
		except TypeError: return metadata
	else:
		return None
	if metadata['author'] == '' or metadata['title'] == '':
		print('No metadata in file, fetching from 3rd party')
		metadata = test_upload(fname)
		if metadata == None: return None
#If author/title are not specified in proper metadata field, it tries to infer them from filename by splitting it by '-', as in 'author - title'.
	if  ' - ' in fname and (isinstance(metadata['author'], str) == False or isinstance(metadata['title'], str) == False):
		fname_data = fname.split(' - ')
		metadata['author'] = fname_data[0]
		metadata['title'] = fname_data[1].split('.')[0]
		if len(metadata['title']) < 2:
			end = len(fname_data)
			fname_data[end-1] = fname_data[end-1].split('.')[0]
			n = 2
			while n < end:
				metadata['title'] = str(metadata['title']) + '. ' + str(fname_data[n])
				n = n+1
#If author/title is not a string, the following test will fail with and exception, so the same steps are executed in both cases.
	if ' - ' in fname and (len(metadata['author']) < 2 or len(metadata['title']) < 2):
		fname_data = fname.split(' - ')
		metadata['author'] = fname_data[0]
		metadata['title'] = fname_data[1].split('.')[0]
		if len(metadata['title']) < 2:
			end = len(fname_data)
			fname_data[end-1] = fname_data[end-1].split('.')[0]
			n = 2
			while n < end:
				metadata['title'] = str(metadata['title']) + '. ' + str(fname_data[n])
				n = n+1
	if '(Author)' in metadata['author'] or '(Editor)' in metadata['author']:
		metadata['author'] = metadata['author'].split('(')[0]
#Discard author/titles that are incorrect
	invalid_titles = ['Gráfico\d+', '[:: wWw.TheDanieX.CoM ::]', 'Microsoft Word', r'Documento\d+', r'(---)+']
	invalid_authors = ['www.intercambiosvirtuales.org', 'www.rasoulallah.net', 'PDFTiger', 'http://iniciativas-opus-dei.evangelizando.org/libros.htm']
	if any(invalid_title in metadata['title'] for invalid_title in invalid_titles):
		metadata['title'] = ''
	if metadata != None: #If metadata exists for this file, format language abreviations to LibGen style.
		if metadata['lang'] == 'es' or metadata['lang'] == 'esp' or metadata['lang'] == 'sp' or metadata['lang'] == 'es-ES':
			metadata['lang'] = 'Spanish'
		elif metadata['lang'] == 'en':
			metadata['lang'] = 'English'
		elif metadata['lang'] == 'cat' or metadata['lang'] == 'ca':
			metadata['lang'] = 'Catalan'
		elif metadata['lang'] == 'it':
			metadata['lang'] = 'Italian'
		elif metadata['lang'] == 'fr':
			metadata['lang'] = 'French'
		elif metadata['lang'] == 'gl':
			metadata['lang'] = 'Galician'
		elif metadata['lang'] == 'pt':
			metadata['lang'] = 'Portuguese'
		elif metadata['lang'] == None or metadata['lang'] == '':
			metadata['lang'] = 'Spanish'
	for item in metadata:
		try:
			metadata[item] = tildes(metadata[item])
		except TypeError as error:
			print('Error', error)
			print(metadata[item])
	metadata['genre'] = str(metadata['genre'][:497]) + '...' if len(metadata['genre']) > 500 else metadata['genre']
	metadata['author'] = str(metadata['author'][:497]) + '...' if len(metadata['genre']) > 500 else metadata['author']
	return metadata

#METADATA READING FUNCTIONS#

def get_pdf_info(fname):
	file = open(fname, 'rb')
	try:
		pdf = PyPDF2.PdfFileReader(file)
		info = pdf.getDocumentInfo()
		info2 = pdf.getXmpMetadata().custom_properties
	except(zlib.error, expat.ExpatError, ValueError, IndexError, AssertionError, PyPDF2.utils.PdfReadError, TypeError, ValueError, KeyError) as error:
		print(error)
		file.close()
		os.system('move "' + fname + '" error')
		return None
	except AttributeError:
		info2 = None
	if pdf.isEncrypted:
		print("File is encrypted")
		file.close()
		os.system('move "' + fname + '" error')
		return None
	metadata = {}
	try:
		metadata['author'] = info['/Author']
		metadata['title'] = info['/Title']
		metadata['date'] = info['/CreationDate'].split(':')[1][:4]
	except(PyPDF2.utils.PdfReadError, ValueError, KeyError, AttributeError, TypeError, IndexError):
		metadata['author'] = ''
		metadata['title'] = ''
		metadata['date'] = ''
	metadata['series'] = ''
	try:
		metadata['genre'] = info['/Keywords']
	except(ValueError, KeyError, AttributeError, TypeError, IndexError, PyPDF2.utils.PdfReadError):
		metadata['genre'] = ''
	try:
		metadata['creator'] = pdf.getXmpMetadata().dc_creator[0]
	except(KeyError, AttributeError, TypeError, IndexError):
		metadata['creator'] = ''
	try:
		metadata['description'] = tildes(pdf.getXmpMetadata().dc_description['x-default'])
	except(KeyError, AttributeError, TypeError, IndexError):
		metadata['description'] = ''
	try:
		metadata['isbn'] = info2['isbn']
	except(KeyError, AttributeError, TypeError, IndexError):
		try:
			metadata['isbn'] = pdf.getXmpMetadata().dc_identifier
		except(AttributeError, TypeError, IndexError):
			metadata['isbn'] = ''
	try:
		metadata['lang'] = pdf.getXmpMetadata().dc_language[0]
	except(KeyError, AttributeError, TypeError, IndexError):
		metadata['lang'] = ''
	try:
		metadata['publisher'] = pdf.getXmpMetadata().dc_publisher[0]
	except(KeyError, AttributeError, TypeError, IndexError):
		metadata['publisher'] = ''
	file.close()
	return metadata

def get_epub_info(fname):
	ns = {
		'n':'urn:oasis:names:tc:opendocument:xmlns:container',
		'pkg':'http://www.idpf.org/2007/opf',
		'dc':'http://purl.org/dc/elements/1.1/'
	}
	# prepare to read from the .epub file
	try:
		zip = zipfile.ZipFile(fname)
	# find the contents metafile
		txt = zip.read('META-INF/container.xml')
		tree = etree.fromstring(txt)
		cfname = tree.xpath('n:rootfiles/n:rootfile/@full-path',namespaces=ns)[0]
	# grab the metadata block from the contents metafile
		cf = zip.read(cfname)
	except zipfile.BadZipFile:
		return None
	try:
		tree = etree.fromstring(cf)
		p = tree.xpath('/pkg:package/pkg:metadata',namespaces=ns)[0]
	except(IndexError, lxml.etree.XMLSyntaxError):
		return None
	# repackage the data
	res = {}
	for s in ['creator','title','publisher','date','language','identifier','subject', 'description', 'series']:
		try:
			res[s] = p.xpath('dc:%s/text()'%(s),namespaces=ns)[0]
		except IndexError:
			res[s] = ''
	res['author'] = res['creator']
	res['genre'] = res['subject']
	res['isbn'] = ''
	res['lang'] = res['language']
	res['date'] = res['date'].split('-')[0]
	return res

def get_fb2_info(fname):
	# prepare to read from the .fb2 file
	file = open(fname, "rb")
	# find the contents metafile
	txt = file.read()
	soup = BeautifulSoup(txt, features="lxml")
	# grab the metadata block from the contents metafile
	description = soup.description
	# repackage the data
	res = {}
	try:
		first_name = str(re.search("first-name>.+<", str(description)).group()).split('>')[1].split('<')[0]
		last_name = str(re.search("last-name>.+<", str(description)).group()).split('>')[1].split('<')[0]
		res['author'] = tildes(first_name + ' ' + last_name)
	except AttributeError as error:
		print(error)
		res['author'] = ""
	try:
		res['title'] = tildes(re.search("book-title>.+<", str(description)).group().split('>')[1].strip('<'))
	except AttributeError:
		res['title'] = ""
	try:
		res['series'] = ''
	except:
		res['series'] = ""
	try:
		res['volume'] = ''
	except:
		res['volume'] = ""
	try:
		res['publisher'] = description.publisher.getText().capitalize()
	except AttributeError:
		res['publisher'] = ""
	try:
		res['date'] = description.date.getText().strip()
	except AttributeError:
		res['date'] = ""
	try:
		res['isbn'] = description.isbn.getText()
	except AttributeError:
		res['isbn'] = ""
	try:
		res['publisher'] = description.publisher.getText()
	except AttributeError:
		res['publisher'] = ""
	try:
		res['lang'] = description.lang.getText()
	except AttributeError:
		res['lang'] = ""
	try:
		res['genre'] = description.genre.getText()
	except AttributeError:
		res['genre'] = ""
	try:
		res['description'] = tildes(description.annotation.getText())
	except AttributeError:
		res['description'] = ""
	file.close
	return res

def get_mobi_info(fname):
	metadata = {}
	book = Mobi(fname)
	book.parse()
	raw_meta = book.config['exth']['records'] #Get this dict by index names, this is where our info is located.
	try: #Get the number for each field and clean the text. Leave blank if nonexistent.
		metadata['author'] = str(raw_meta[100]).strip("b'")
	except KeyError:
		metadata['author'] = ''
	try:
		metadata['genre'] = str(raw_meta[105]).strip("b'")
	except KeyError:
		metadata['genre'] = ''
	try:
		metadata['isbn'] = str(raw_meta[104]).strip("b'")
	except KeyError:
		metadata['isbn'] = ''
	try:
		metadata['lang'] = str(raw_meta[524]).strip("b'")
	except KeyError:
		metadata['lang'] = ''
	try:
		metadata['title'] = str(raw_meta[503]).strip("b'")
	except KeyError:
		metadata['title'] = ''
	try:
		metadata['publisher'] = str(raw_meta[101]).strip("b'")
	except KeyError:
		metadata['publisher'] = ''
	try:
		metadata['date'] = str(raw_meta[106]).strip("b'")[:4]
	except KeyError:
		metadata['date'] = ''
	try:
		metadata['description'] = str(raw_meta[103]).strip("b'")
	except KeyError:
		metadata['description'] = ''
	metadata['series'] = ''
	return metadata



#Can expand with the following if needed:

#def get_cbz_info(fname):
#def get_cbr_info(fname):
#def get_djvu_info(fname):

def tildes(string): #Corrects wrongly formated tilde and other characters for a given string
		string = re.sub(re.escape('\\\\'), re.escape('\\'), string)
		string = re.sub('a¡', 'á', string)
		string = re.sub('ã¡', 'á', string)
		string = re.sub('A¡', 'á', string)
		string = re.sub('Ã¡', 'á', string)
		string = re.sub('&#225;', 'á', string)
		string = re.sub(re.escape('\\xc3\\xa1'), 'á', string)
		string = re.sub(re.escape('\\xe1'), 'á', string)
		string = re.sub('A©', 'é', string)
		string = re.sub('a©', 'é', string)
		string = re.sub('ã©', 'é', string)
		string = re.sub('Ã©', 'é', string)
		string = re.sub('&#233;', 'é', string)
		string = re.sub(re.escape('\\xc3\\xa9'), 'é', string)
		string = re.sub(re.escape('\\xe9'), 'é', string)
		string = re.sub(re.escape('\xe9'), 'é', string)
		string = re.sub('\\xe9', 'é', string)
		string = re.sub('Ã«', 'ë', string)
		string = re.sub('ã­', 'í', string)
		string = re.sub('Ã­', 'í', string)
		string = re.sub('a­', 'í', string)
		string = re.sub('A­', 'í', string)
		string = re.sub('&#237;', 'í', string)
		string = re.sub(re.escape('\\xc3\\xad'), 'í', string)
		string = re.sub(re.escape('\\xed'), 'í', string)
		string = re.sub('a³', 'ó', string)
		string = re.sub('A³', 'ó', string)
		string = re.sub('ã³', 'ó', string)
		string = re.sub('Ã³', 'ó', string)
		string = re.sub('&#243;', 'ó', string)
		string = re.sub(re.escape('\\xc3\\xb3'), 'ó', string)
		string = re.sub(re.escape('\\xf3'), 'ó', string)
		string = re.sub(re.escape('\xf3'), 'ó', string)
		string = re.sub('\\xf3', 'ó', string)
		string = re.sub('\xf3', 'ó', string)
		string = re.sub('aº', 'ú', string)
		string = re.sub('ãº', 'ú', string)
		string = re.sub('Ãº', 'ú', string)
		string = re.sub('Aº', 'ú', string)
		string = re.sub('&#250;', 'ú', string)
		string = re.sub('Ã', 'Ú', string)
		string = re.sub(re.escape('\\xc3\\xba'), 'Ú', string)
		string = re.sub('a±', 'ñ', string)
		string = re.sub('ã±', 'ñ', string)
		string = re.sub('A±', 'ñ', string)
		string = re.sub('Ã±', 'ñ', string)
		string = re.sub('�', 'ñ', string)
		string = re.sub(re.escape('\\xf1'), 'ñ', string)
		string = re.sub(re.escape('\\xc3\\xb1'), 'ñ', string)
		string = re.sub(re.escape('\\xc2\\xbf'), '¿', string)
		string = re.sub(re.escape('\\xc2\\xbb'), '»', string)
		string = re.sub(re.escape('\\xc2\\xab'), '«', string)
		string = re.sub('&#231;', 'ç', string)
		string = re.sub(re.escape('\\n'), ' ', string)
		string = re.sub(re.escape('\n'), ' ', string)
		string = re.sub(re.escape('\\r'), ' ', string)
		string = re.sub(re.escape('\r'), ' ', string)
		string = re.sub('Å½', 'Ž', string)
		string = re.sub('Å¾', 'ž', string)
		string = re.sub('  ', ' ', string)
		string = re.sub(' &', ';', string)
		return string

def brief(filelist): #Makes a .tsv file with file names and their metadata
	brief = open('ZZFiles.tsv', 'w+')
	global fhash
	brief.write('FILE	MD5	AUTHOR	TITLE	YEAR	PUBLISHER	ISBN	LANGUAGE	GENRE\n')
	for fname in filelist:
		print('File:', fname)
		fhash = str(hashlib.md5(fname.read()).hexdigest())
		metadata = get_fb2_info(fname)
		print(metadata)
		brief.write(fname + '	' + fhash + '	' + metadata['author'] + '	' + metadata['title'] + '	' + metadata['date'] + '	' + metadata['publisher'] + '	' + metadata['isbn'] + '	' + metadata['lang'] + '	' + metadata['genre'] + '\n')
		print()
	brief.close


#FILE HANDLING FUNCTIONS#

def setup(): #Checks for folders that the program uses and creates them if necessary
	if os.path.exists('uploaded'):
		pass
	else:
		os.mkdir('uploaded')
	if os.path.exists('error'):
		pass
	else:
		os.mkdir('error')
	if os.path.exists('no_metadata'):
		pass
	else:
		os.mkdir('no_metadata')
	if os.path.exists('comics'):
		pass
	else:
		os.mkdir('comics')

def make_filelist(): #Makes a list with the names of the files in the program directory
	filelist = os.popen('chcp 65001 & dir /B *.*').read()
	filelist = filelist.split('\n')
	filelist.pop(0)
	filelist.pop(len(filelist) - 1)
	filelist.remove('uploaded')
	filelist.remove('no_metadata')
	filelist.remove('error')
	filelist.remove('comics')
	return filelist

def get_hashes(filelist): #Prints the MD5 hashes of files in a given list if they are in the program's directory
	for fname in filelist:
		with open(fname, 'rb').read() as file:
			print(hashlib.md5(file).hexdigest())

def split_errors(): #(For Libgen's own batch uploader) Moves files that returned error when batch uploaded if given a proper error list from the site in a file named ERRORS.txt
	filelist = open('ERRORS.txt', 'r').read().split('\n')
	for file in filelist:
		file = file.split('file ')[0]
		file = file.split(" This ")[0].split(" The ")[0] + '.fb2'
		file = tildes(file)
		print(file)
		os.system('move "' + file + '" error')
		print()

def rename(filelist): #(For Libgen's own batch uploader) Renames files of a given filelist to batch uploader format
	for file in filelist:
		print('File:', file)
		metadata = get_metadata(file)
		if metadata == None: continue
		Author = str(metadata['author'])
		Title = str(metadata['title'])
		if Title == '':
			Title = str(file).strip('.')
		Series = ''
		Volume = ''
		Publisher = str(metadata['publisher'])
		Year = str(metadata['date'])
		ISBN = str(metadata['isbn'])
		Publishing = ''
		Language = str(metadata['lang'])
		NewFileName = str(Author + ';' + Title + ';' + Series + ';' + Volume + ';' + Publisher + ';' + Year + ';' + ISBN + ';' + Publishing + ';' + Language + metadata['extension'])
		NewFileName = tildes(NewFileName)
		NewFileName = re.sub('[\/:*?"<>|]', '', NewFileName)
		NewFileName = NewFileName.replace("\\", "").replace("\t", "").replace("\n", "").replace("\r", "").replace("_", "")
		print('Rename:', NewFileName)
		try:
			os.rename(file, NewFileName)
		except FileExistsError:
			continue
		print()

def categorize(string): #Returns category (fiction/non-fiction) for a string by matching it to genres regex variables
	global fiction
	global non_fiction
	fic = False
	nof = False
	for item in fiction:
		result = re.match(item, string)
		if result != None:
			print(string, item)
			return "fiction"
	for item in non_fiction:
		result = re.match(item, string)
		if result != None:
			print(string, item)
			return "non-fiction"
	for item in comics:
		result = re.match(item, string)
		if result != None:
			print(string, item)
			return "comic"
	return None

def verify(fname): #Checks a filename and returns false if the file extension is among the accepted ones (to tell if the file is a book or not)
	fname_part = fname.split('.')
	fext = fname_part[len(fname_part) - 1]
	for format in valid_formats:
		if format.lower() == fext.lower():
			return True
		else:
			continue
	return False

def auth_categorize(string): #Returns category (fiction/non-fiction) for a string by matching it to authors regex variables
	global fiction
	global non_fiction
	fic = False
	nof = False
	for item in authors_fic:
		result = re.match(item, string)
		if result != None:
			print(string, item)
			return "fiction"
	for item in authors_non:
		result = re.match(item, string)
		if result != None:
			print(string, item)
			return "non-fiction"
	return None

def categorize_sort(filelist): #(For Libgen's own batch uploader) Moves files of a given filelist into 'fiction' and 'non-fiction' directories
	uncategorized = []
	for file in filelist:
		print()
		print(file)
		metadata = get_metadata(file)
		if metadata == None or metadata == '':
			continue
		genre = metadata['genre']
		print('Genre:', genre)
		category = categorize(genre)
		print(category)
		if category == "non-fiction":
			os.system('move "' + file + '" non_fiction')
		elif category == "fiction":
			os.system('move "' + file + '" fiction')
		elif category == "comic":
			os.system('move "' + file + '" comics')
		else:
			uncategorized.append(genre)
	while '' in uncategorized: uncategorized.remove('')
	uncategorized = list(dict.fromkeys(uncategorized))
	print(uncategorized)

#LIBGEN FUNCTIONS

def categorize_upload(filelist): #Takes files from a given filelist and calls the proper upload function
	global uncategorized
	global uncategorized_authors
	try:
		for fname in filelist:
			print('File: ' + fname)
			#Only works with uploadable file formats
			test = verify(fname)
			if test == False:
				print("Invalid format")
				print()
				continue
			#Checks that the filesize is not lower than allowed
			try:
				with open(fname, 'rb') as file:
					fsize = file.seek(0,2)
					print('Size: ' + str(fsize / 1000000) + ' MB')
					if fsize <= 30720:
						print('File too small')
						file.close()
						os.system('move "' + fname + '" error')
						continue
			except PermissionError:
				continue
			metadata = get_metadata(fname)
			#If there is not enough metadata in the file, it moves it to a no_metadata directory
			if metadata == None or metadata == '' or len(metadata['lang']) < 2 or len(metadata['title']) < 2 or len(metadata['author']) < 2:
				print('No metadata')
				os.system('move "' + fname + '" no_metadata')
				print()
				continue
			print('Author:', metadata['author'])
			print('Title:', metadata['title'])
			collection = classify(fname, metadata)
			if collection == None:
				print()
				continue
			uploaded1 = check_hash(fname)
			if uploaded1 == True:
				print()
				continue
			uploaded2 = search_book(fname, metadata['title'], metadata['author'])
			if uploaded2 == True:
				print()
				continue
			else:
				pass
			if collection == 'fiction':
				upload_fiction(fname, metadata)
			if collection == 'non-fiction':
				upload(fname, metadata)
			if collection == 'comic':
				os.system('move "' + fname + '" comics')
			print()
	except KeyboardInterrupt:
		print('Terminating')
	while '' in uncategorized: uncategorized.remove('')
	uncategorized = list(dict.fromkeys(uncategorized))
	uncategorized_authors = list(dict.fromkeys(uncategorized_authors))
	print(uncategorized)
	print(uncategorized_authors)
	quit()
#Makes a list of uncategorized genres so devs can further expand the variables to include them

def search_book(fname, title, author): #Checks that the book is not already uploaded by using its title and author
	session = requests.session()
	formatted_title = title.replace(' ', '+').replace(':', '%3A').replace('.', '&#46')
	print(formatted_title)
	table = []
	while table == []:
		try:
			nonfic_result = session.get('http://libgen.rs/search.php?req=' + formatted_title)
			parsed_html = BeautifulSoup(nonfic_result.text, features="lxml")
			table = parsed_html.body.find_all("table")
			nonfic_result = table[1].tr.td.font.contents[0]
			found_files = int(nonfic_result.split(' ')[0])
		except IndexError as error:
			print(error)
			if 'The search query length should be not less than 2 characters' in parsed_html.body.h1:
				print('Title too short. Omitting')
				return False
	if found_files == 0:
		print('Not found in non-fiction collection')
		pass
	elif found_files >= 1:
		print('Title found in non-fiction collection')
		print('Checking author')
		table = parsed_html.body.find("table", attrs={'class':'c'}).find_all('tr')
		for row in table:
			try:
				res_auth = row.find_all('td')[1].a.contents[0]
				if res_auth == author:
					print('Author found')
					print('Author in file metadata: ', author, '; Author found:', res_auth)
					os.system('move "' + fname + '" uploaded')
					return True
			except IndexError:
				print('Parsing error')
		print('Author not found')
	fiction_result = session.get('http://libgen.rs/fiction/?q=' + formatted_title)
	parsed_html = BeautifulSoup(fiction_result.text, features="lxml")
	fiction_result = parsed_html.body.find("div", attrs={'class':'catalog_paginator'})
	if fiction_result == None:
		print('Not found in fiction collection')
		pass
	elif fiction_result != None:
		print('Title found in fiction collection')
		print('Checking author')
		table = parsed_html.body.table.tbody.find_all('tr')
		for row in table:
			try:
				res_auth = row.td.ul.li.a.contents[0]
				if res_auth == author:
					print('Author found')
					print('Author in file metadata: ', author, '; Author found:', res_auth)
					os.system('move "' + fname + '" uploaded')
					return True
			except AttributeError:
				print('Parsing error')
			except IndexError:
				return False
		print('Author not found')
	return False

def check_hash(fname): #Checks if a given file is already uploaded in various LibGen mirrors using its MD5 hash
	session = requests.session()
	session.trust_env = False
	session.headers = libgen_headers
	with open(fname, "rb") as file:
		global fhash
		fhash = str(hashlib.md5(file.read()).hexdigest())
	print("MD5 HASH: " + fhash)
	print("Checking...")
	print("DOMAIN NAME	NON-FIC	FICTION")
	try:
		response5 = session.get('http://libgen.lc/item/index.php?md5=' + fhash).status_code
		response6 = session.get('http://libgen.lc/foreignfiction/item/index.php?md5=' + fhash).status_code
		print('libgen.lc	' + str(response5) + '	' + str(response6))
		response = session.get('http://library.bz/main/uploads/' + fhash).status_code
		response2 = session.get('http://library.bz/fiction/uploads/' + fhash).status_code
		print('library.bz	' + str(response) + '	' + str(response2))
		response3 = session.get('http://libgen.rs/book/index.php?md5=' + fhash).status_code
		response4 = session.get('http://libgen.rs/fiction/' + fhash).status_code
		print('libgen.rs	' + str(response3) + '	' + str(response4))
	except requests.exceptions.ConnectionError as error:
		print(error)
	session.trust_env = True
	session.close()
	if response == 200 or response2 == 200 or response3 == 200 or response4 == 200 or response5 == 200 or response6 == 200:
		print("Already uploaded")
		file.close()
		os.system('move "' + fname + '" uploaded')
		return True
	elif response != 200 or response2 != 200 or response3 != 200 or response4 != 200 or response5 != 200:
		print("Not already uploaded")
		return False

def classify(fname, metadata):
	global uncategorized
	global uncategorized_authors
	genre = str(metadata['genre'])
	title = str(metadata['title'])
	print('Genre:', genre)
	collection = categorize(genre)
	#Decides which collection the book belongs to according to fiction and non-fiction global variables. If there is no genre for the book, it infers it from its title and author
	if genre == '' or genre == r' +' or genre == None or genre == 'NONE' or genre == 'None' or genre == 'none' or genre == '-':
		print('No genre')
		print('Category by author')
		collection = auth_categorize(str(metadata['author']))
		if collection == None:
			print('No match found for author')
			print('Category by title')
			collection = categorize(str(metadata['title']))
			if collection == None:
				print('No match found for title')
				os.system('move "' + fname + '" no_metadata')
				print()
	if collection == None and genre != r' +':
		print('No category for genre')
		uncategorized.append(genre)
		uncategorized.append(title)
		uncategorized_authors.append(metadata['author'])
	if '.cbz' in fname or '.cbr' in fname:
		collection = 'comic'
	print("Collection:", collection)
	return collection

def upload_fiction(fname, metadata): #Function for uploading fiction content
	session = requests.session()
	session.headers = libgen_headers
	try:
		file = open(fname, "rb")
	except PermissionError as error:
		print(error)
		return
	print('Uploading...')
	files = {'file':file}
	try:
		response = session.post('https://library.bz/fiction/upload/', files=files)
	except requests.exceptions.ConnectionError as error:
		print("Error: " + str(error))
		time.sleep(120)
		response = session.post('https://library.bz/fiction/upload/', files=files)
	parsed_html = BeautifulSoup(response.text, features="lxml")
	form_error = parsed_html.body.find('div', attrs={'class':"form_error"})
	if response.status_code != 200 or 'Unable to process the uploaded file' in form_error:
		print('Upload Failed: file not uploaded')
		file.close()
		os.system('move "' + fname + '" error')
		print()
		return None
	try:
		metadata['cover'] = str(parsed_html.body.find('input', attrs={'name':'cover'})['value'])
	except AttributeError as error:
		print(error)
		print()
		file.close()
		return
	except IndexError:
		metadata['cover'] = ''
	global fhash
	new_url = 'https://library.bz/fiction/uploads/new/' + str(fhash)
	form = make_form_fiction(fname, metadata)
	if form == None:
		print("No metadata")
		return
	session.headers.update({'Referer':new_url, 'Content-Type':'application/x-www-form-urlencoded','Content-Length':str(len(form))})
	confirm = session.post(new_url, data=form)
	if confirm.status_code != 200:
		print('Submission Failed: ' + str(confirm.status_code))
		file.close()
		os.system('move "' + fname + '" error')
	elif confirm.status_code == 200:
		print('Submission Succesfull')
	file.close()
	if 'The record has been successfully saved.' in confirm.text:
		print("Upload Succesfull")
		os.system('move "' + fname + '" uploaded')
	elif 'value length is below the minimum required' in confirm.text or 'Unable to process the uploaded file' in confirm.text or 'The record is not found' in confirm.text:
		print("Upload Failed")
		os.system('move "' + fname + '" error')
	elif 'Database error' in confirm.text:
		print('Database Error')
	elif 'invalid ISBN format' in confirm.text:
		print('Invalid ISBN, resubmitting...')
		form = make_form_fiction(fname, metadata, False)
		confirm = session.post(new_url, data=form)
		if 'record has been successfully saved' in confirm.text:
			print("Upload Succesfull")
			os.system('move "' + fname + '" uploaded')
		else:
			print(form)
			print(BeautifulSoup(confirm.text, features="lxml").body.find_all('div', attrs={'class':'form_error'}))
	print()
	del session.headers['Referer']
	del session.headers['Content-Type']
	del session.headers['Content-Length']
	session.close()
	return

def upload(fname, metadata): #Function for uploading non-fiction content
	session = requests.session()
	session.headers = libgen_headers
	try:
		file = open(fname, "rb")
	except PermissionError as error:
		print(error)
		return
	print('Uploading...')
	files = {'file':file}
	try:
		response = session.post('https://library.bz/main/upload/', files=files)
	except requests.exceptions.ConnectionError as error:
		print("Error: " + str(error))
		time.sleep(120)
		response = session.post('https://library.bz/main/upload/', files=files)
	parsed_html = BeautifulSoup(response.text, features="lxml")
	form_error = parsed_html.body.find('div', attrs={'class':"form_error"})
	if response.status_code != 200 or 'Unable to process the uploaded file' in form_error:
		print('Upload Failed: file not uploaded')
		file.close()
		os.system('move "' + fname + '" error')
		print()
		return None
	try:
		metadata['cover'] = str(parsed_html.body.find('input', attrs={'name':'cover'})['value'])
	except AttributeError as error:
		print(error)
		print()
		file.close()
		return
	except IndexError:
		metadata['cover'] = ''
	global fhash
	new_url = 'https://library.bz/main/uploads/new/' + str(fhash)
	form = make_form(fname, metadata)
	if form == None:
		print("No metadata")
		return
	session.headers.update({'Referer':new_url, 'Content-Type':'application/x-www-form-urlencoded','Content-Length':str(len(form))})
	confirm = session.post(new_url, data=form)
	file.close()
	if 'The record has been successfully saved.' in confirm.text:
		print("Upload Succesfull")
		os.system('move "' + fname + '" uploaded')
	elif 'Unable to process the uploaded file' in confirm.text or 'The record is not found' in confirm.text:
		print("Upload Failed")
		os.system('move "' + fname + '" error')
	elif 'invalid ISBN format' in confirm.text:
		print('Invalid ISBN, resubmitting...')
		form = make_form(fname, metadata, False)
		confirm = session.post(new_url, data=form)
		if 'record has been successfully saved' in confirm.text:
			print("Upload Succesfull")
			os.system('move "' + fname + '" uploaded')
		else:
			print(form)
			print(BeautifulSoup(confirm.text, features="lxml").body.find_all('div', attrs={'class':'form_error'}))
	print()
	del session.headers['Referer']
	del session.headers['Content-Type']
	del session.headers['Content-Length']
	session.close()
	return

def test_upload(fname): #Function for uploading to non-fiction content and fetching metadata from 3rd parties
	session = requests.session()
	session.headers = libgen_headers
	if check_hash(fname) == True: return None
	try:
		file = open(fname, "rb")
	except PermissionError as error:
		print(error)
		return None
	print('Uploading...')
	files = {'file':file}
	try:
		response = session.post('https://library.bz/main/upload/', files=files)
	except requests.exceptions.ConnectionError as error:
		print("Error: " + str(error))
		time.sleep(120)
		response = session.post('https://library.bz/main/upload/', files=files)
	parsed_html = BeautifulSoup(response.text, features="lxml")
	form_error = parsed_html.body.find('div', attrs={'class':"form_error"})
	if response.status_code != 200 or 'Unable to process the uploaded file' in form_error:
		print('Upload Failed: file not uploaded')
		print(form_error)
		file.close()
		os.system('move "' + fname + '" error')
		print()
		return None
	print('File uploaded, fetching metadata')
	cover = str(parsed_html.body.find('input', attrs={'name':'cover'})['value'])
	isbn = str(parsed_html.body.find('input', attrs={'name':'isbn'})['value'])
	if isbn == "": return None
	global fhash
	new_url = 'https://library.bz/main/uploads/new/' + str(fhash)
	print("Fetching metadata from 3rd party...")
	form = make_form_fetching(isbn, cover)
	session.headers.update({'Referer':new_url, 'Content-Type':'application/x-www-form-urlencoded','Content-Length':str(len(form))})
	response = session.post(new_url, data=form)
	parsed_html = BeautifulSoup(response.text, features="lxml")
	metadata = {}
	metadata['title'] = str(parsed_html.body.find('input', attrs={'name':'title'})['value'])
	metadata['author'] = str(parsed_html.body.find('input', attrs={'name':'authors'})['value'])
	metadata['volume'] = str(parsed_html.body.find('input', attrs={'name':'volume'})['value'])
	metadata['lang'] = str(parsed_html.body.find('input', attrs={'name':'language'})['value'])
	metadata['series'] = str(parsed_html.body.find('input', attrs={'name':'series'})['value'])
	metadata['date'] = str(parsed_html.body.find('input', attrs={'name':'year'})['value'])
	metadata['publisher'] = str(parsed_html.body.find('input', attrs={'name':'publisher'})['value'])
	metadata['isbn'] = str(parsed_html.body.find('input', attrs={'name':'isbn'})['value'])
	metadata['genre'] = str(parsed_html.body.find('input', attrs={'name':'tags'})['value'])
	metadata['description'] = str(parsed_html.body.find('textarea', attrs={'name':'description'}).contents)
	collection = classify(fname, metadata)
	if collection == 'non-fiction':
		session.headers.update({'Referer':new_url, 'Content-Type':'application/x-www-form-urlencoded','Content-Length':str(len(form))})
		confirm = session.post(new_url, data=form)
		file.close()
		if 'The record has been successfully saved.' in confirm.text:
			print("Upload Succesfull")
			os.system('move "' + fname + '" uploaded')
		elif 'Unable to process the uploaded file' in confirm.text or 'The record is not found' in confirm.text:
			print("Upload Failed")
			os.system('move "' + fname + '" error')
		elif 'invalid ISBN format' in confirm.text:
			print('Invalid ISBN, resubmitting...')
			form = make_form(fname, metadata, False)
			confirm = session.post(new_url, data=form)
			if 'record has been successfully saved' in confirm.text:
				print("Upload Succesfull")
				os.system('move "' + fname + '" uploaded')
			else:
				print(form)
				print(BeautifulSoup(confirm.text, features="lxml").body.find_all('div', attrs={'class':'form_error'}))
		print()
	del session.headers['Referer']
	del session.headers['Content-Type']
	del session.headers['Content-Length']
	session.close()
	return metadata

def make_form(file, metadata, isbn = True): #Function for making an upload form for non-fiction content
	print("Making form...")
	if metadata == None:
		return None
	if len(metadata['publisher']) > 100:
		metadata['publisher'] = ''
	form = {'metadata_source':'', 'local':'',
	'metadata_query':'',
	'title':str(metadata['title']),
	'volume':'',
	'authors':str(metadata['author']),
	'language':str(metadata['lang']), 
	'language_options':'',
	'edition':'',
	'series':str(metadata['series']),
	'pages':'',
	'year':metadata['date'],
	'publisher':metadata['publisher'],
	'city':'',
	'periodical':'',
	'isbn':metadata['isbn'],
	'issn':'',
	'doi':'',
	'gb_id':'',
	'asin':'',
	'ol_id':'',
	'ddc':'',
	'lcc':'',
	'udc':'',
	'lbc':'',
	'topic':'',
	'tags':metadata['genre'],
	'cover':metadata['cover'],
	'description':str(metadata['description']),
	'toc':'',
	'scan':0,
	'dpi':'',
	'dpi_select':'',
	'searchable':1,
	'paginated':0, 
	'page_orientation':0,
	'colored':1,
	'cleaned':1,
	'bookmarks':0,
	'file_source':'',
	'file_source_issue':'',
	'file_commentary':''
	}
	if isbn == False:
		form['isbn']=''
	form = urlencode(form, quote_via=quote_plus)
	return form

def make_form_fiction(file, metadata, isbn=True): #Function for making an upload form for fiction content
	print("Making form...")
	if metadata == None:
		return None
	if len(metadata['publisher']) > 100:
		metadata['publisher'] = ''
	form = {
	"metadata_source": "local",
	"metadata_query": "",
	"title": str(metadata['title']),
	"authors": str(metadata['author']),
	"language": str(metadata['lang']),
	"language_options": "",
	"edition": "",
	"series": str(metadata['series']),
	"pages": "",
	"year": str(metadata['date']),
	"publisher": str(metadata['publisher']),
	"isbn": str(metadata['isbn']),
	"gb_id": "",
	"asin": "",
	"cover": metadata['cover'],
	"description": str(metadata['description']),
	"file_source": "",
	"file_source_issue": "",
	"file_commentary": ""
	}
	if isbn == False:
		form['isbn']=''
	form = urlencode(form, quote_via=quote_plus)
	return form

def make_form_fetching(isbn, cover): #Function for making a form fetching data from a third party instead of using the file's metadata.
	form = {
	"metadata_source":"worldcat",
	"metadata_query":isbn,
	"fetch_metadata":"Fetch",
	"title":"",
	"volume":"",
	"authors":"",
	"language":"",
	"language_options":"",
	"edition":"",
	"series":"",
	"pages":"",
	"year":"",
	"publisher":"",
	"city":"",
	"periodical":"",
	"isbn":isbn,
	"issn":"",
	"doi":"",
	"gb_id":"",
	"asin":"",
	"ol_id":"",
	"ddc":"",
	"lcc":"",
	"udc":"",
	"lbc":"",
	"topic":"",
	"tags":"",
	"cover":cover,
	"description":"",
	"toc":"",
	"scan":"",
	"dpi":"",
	"dpi_select":"",
	"searchable":"",
	"paginated":"",
	"page_orientation":"",
	"colored":"",
	"cleaned":"",
	"bookmarks":"",
	"file_source":"",
	"file_source_issue":"",
	"file_commentary":""}
	form = urlencode(form, quote_via=quote_plus)
	return form


#MAIN PROGRAM SEQUENCE#
setup()
filelist = make_filelist()
categorize_upload(filelist)

#ORDERING LISTS
#non_fiction.sort()
#print(non_fiction)

#TEST TILDE REPLACING
#string = input('Text to convert: ')
#print(tildes((string)))

#TEST REGEX MATCHING
#string = input('Get collection for: ')
#print("As genre: " + str(categorize(string)))
#print("As author: " + str(auth_categorize(string)))
