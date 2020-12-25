
from datetime import date
import os

# Error Codes

NOERROR = 240  # All good
EBUILD = 241  # Building problems
ENOBRDGNET = 242  # docker bridge network not found
EACCESS = 243  # Permission denied
EMSCONN = 244  # Metasploit container not connecting, is it running?
EMSPASS = 245  # Authentication, password does not match'
ENOPERM = 246  # User does not belong docker group
EMODNR = 247  # Module not runnable, try with autoauditor.py
EBADREPFMT = 248  # Bad report format
ECONN = 249  # Connection error, can not connect to HLF peer
EBADNETFMT = 250  # Bad network configuration file (format)
EMISSINGARG = 251  # Query missing argument
ENOENT = 252  # No such file or directory
EBADRCFMT = 253  # Bad resources script (format)
EINTR = 254  # Interrupted system call
EDOCKER = 255  # Docker API error
EHLFCONN = 256  # Hyperledger Fabric Error

# Metasploit

DEF_MSFRPC_PWD = 'dummypass'

# Log Messages

MSSTAT = "Metasploit image status:"
MSEXIST = "Metasploit image status: exists."
MSDOWN = "Metasploit image status: does not exist, downloading ..."
MSDONE = "Metasploit image status: does not exist, downloading ... done"
MSCSTAT = "Metasploit container status:"
MSCR = "Metasploit container status: running."
MSCNR = "Metasploit container status: not running."
MSCSTART = "Metasploit container status: not running, starting ..."
MSCDONE = "Metasploit container status: not running, starting ... done"
MSSTOP = "Stopping metasploit container ..."
MSSTOPPED = "Stopping metasploit container ... done"
MSSTOPERR = "Stopping metasploit container ... error"
MSNR = "Stopping metasploit container ... not running"
VPNSTAT = "VPN client image status:"
VPNEXIST = "VPN client image status: exists."
VPNDOWN = "VPN client image status: does not exist, downloading ..."
VPNDONE = "VPN client image status: does not exist, downloading ... done"
VPNCSTAT = "VPN client container status:"
VPNCR = "VPN client container status: running."
VPNCNR = "VPN client container status: not running."
VPNCSTART = "VPN client container status: not running, starting ..."
VPNCDONE = "VPN client container status: not running, starting ... done"
VPNSTOP = "Stopping VPN client container ..."
VPNSTOPPED = "Stopping VPN client container ... done"
VPNSTOPERR = "Stopping VPN client container ... error"
VPNNR = "Stopping VPN client container ... not running"
ATNET = "Removing attacker_network ..."
ATNETRM = "Removing attacker_network ... done"
ATNETNF = "Removing attacker_network ... not found"
ATNETAEND = "Removing attacker_network ... error. Active endpoints."
GENREP = "Generating report ..."
GENREPDONE = "Generating report ... done"
MOD_TYPES = ['auxiliary', 'encoder', 'exploit', 'nop', 'payload', 'post']
RC_TEMPLATE = '../config/rc.template.json'
NET_TEMPLATE = '../config/network.template.json'

# GUI

WRAP_T_SZ = 70

ICO_FILE = (b'iVBORw0KGgoAAAANSUhEUgAAABgAAAAgCAYAAAAIXrg4AAAABHNCSVQICAgIfAhk'
            b'iAAAAAlwSFlzAAAA7AAAAOwBeShxvQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3Nj'
            b'YXBlLm9yZ5vuPBoAAACFSURBVEiJ7dC9DkAwGEbhQ8XghlyZwWgzuN4murCUNJTo'
            b'3+Q7iaGJvE9agBlYgS3wO9LAyEsx4y5wnKcnIGbcB2z2NYoCXiQ3cENKACdSXX4O'
            b'qXKAp8bSgG4ixwFawDiQtzoBGCzyWsoTfSrlBgIIIIAAAgjwM8AU3F8V0AE9oDKP'
            b'G2DZAZVbdv9fKQUhAAAAAElFTkSuQmCC')
ICO_FOLDER = (b'iVBORw0KGgoAAAANSUhEUgAAACAAAAAYCAYAAACbU/80AAAABHNCSVQICAgIfA'
              b'hkiAAAAAlwSFlzAAAA7AAAAOwBeShxvQAAABl0RVh0U29mdHdhcmUAd3d3Lmlu'
              b'a3NjYXBlLm9yZ5vuPBoAAABtSURBVEiJ7dYxEoAgDETRLwXntgzn4Gww3kILoL'
              b'ESjKZJZrah2Ue3ABFIQAXOh9lRPJko/gQx8/N7RAOwWq6GeAtYSenwuPUHq0vW'
              b'gMMaQLAsd4ADHOAABzhgAKphfwlANgRkaLNcaDPp90l2AYuzfIE6Q1SuAAAAAE'
              b'lFTkSuQmCCiVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAABHNC'
              b'SVQICAgIfAhkiAAAAAlwSFlzAAAA7AAAAOwBeShxvQAAABl0RVh0U29mdHdhcm'
              b'UAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAB0SURBVFiF7dYxEoAgDETRLwXntsRz'
              b'cDYYb6EF2FgJgrHYnUmTZl+6gKKABzYgA8fDWUcCQkPxFETL5fcJIwC95cMQbw'
              b'E9kyrcL3Vhlc0asFsDcJblAggggAACCHABsmF/ckA0BEQob3mgvEmfv2TTT1R+'
              b'nxOQcHyB+7o6JAAAAABJRU5ErkJggg==')
ICO_PLAY = (b'iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAABHNCSVQICAgIfAhk'
            b'iAAAAAlwSFlzAAAOxAAADsQBlSsOGwAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3Nj'
            b'YXBlLm9yZ5vuPBoAAATTSURBVGiBxdrbq1ZFGAbwn5/uPOzUpPaWoiSCPHRRlFYg'
            b'aJmVZWpEdRFBQVl4qAiSzkEXluZOELqoCIK6rL9AKw8dSDvYWUtSSYvKMnVrprXd'
            b'XxezlrO+z31Y6zvs/cBisWbNPPPOrJl5n3lnDdEYtON6XIqLMQHjMRZdOIzfsBff'
            b'4GN8gH0Nqr8mjMUSbMEJlAteXdiEpRhTqxFDaijThsexCKOq3nXhO+zAXziYpI/D'
            b'mZiEKRhaVa4Tr2OFJn6VYVgmDIdsT/6EDkzHiBw8rZiBVdhZxXVI6JyWBttuEj6r'
            b'quxDYdzX8hVTDMENWFfF/Skm18FbgQVCz6Tk23Bdo8gzuBZfZ+o5jPn1kt4vTtAT'
            b'eA7D6yXtA6dhpTCX0om+uFaypehOiA5iXgMMzIt54lzrxsKiBAvEnv8TUxtpXU5c'
            b'hv3i1889nKaIre/EJc2wLicuF+ffQUzsr0CLuNp0YW4zrcuJm8Wh/IlTfUgFnhRX'
            b'geebblp+rBTtWtZbpvHCkCnjK2FFyIOZeAa36ad36sAIbBeX17aeMq0RW3lNTuKH'
            b'VDqgL3F1fbb2itmZejqqX44Re39tAdJ9KhuQXm/j/LrM7RkbEv4jqgTgA5nK5+Qk'
            b'G5Yps1yYP0cyaf8k6a0NMDzFnAx/hYN7P0n8UX5tk23A00naOXhVpbz+RfDopfps'
            b'J+HYnfBuThPbRde9qgBZTw1IMU0Qe9UCbXqNhmexQnRubYTVI61kRgGivhpA+JK3'
            b'C3I7zdeNt4QdW62YmeG7A15MHo7Lp+dT9NeAFKPwrDAn0vx/J2lF6kvRgmMyq9Ha'
            b'5OHzgkR5G5DiPLwpetUy9uCugvXCF0n5dSXxc+6qgagI9grGzhZ0P6FRb2A9LirA'
            b'9UNyn1DC2cnDzw0wMg82CEpzsaB0YZagc/I24o/k3lYSx+HRRlmYAyfwiqAu1yTP'
            b'rbgvZ/nO5H56SRjLhKV0sFHOme+kzSVBHBHiPAOFoUJYZgceTp6P4LWc5Ucm9+Ml'
            b'cTy1N9LCPjALW/EyzkrSNuBKQXHmwbnJ/deS4GjIsdupE+kyul4IPxJWprsF9but'
            b'ANcFyX0PrBbG3lFxbOXBYDmykfhXRvrcmSEuolUGS0rMyPDdShj7qXpcXoCoPzH3'
            b'UeZ9I8Vch7hnPzlvNyeJO+WXvYMlp3clvBuzLxZnKswbNqze0Dyl+RuauRn+JdkX'
            b'YzOVry9AONBbynfFGNHo6pfp2CoLgisPHlRpeDM39dnt5OqeMrSJEbnt8gdxByKs'
            b'Mhzfir3fY1iFEDRKW7miScbUghdEux7tK+NQYblL1+wFTTetf2QDzVvkcLYThc9U'
            b'FgKr05ppXT+YpjLQPClvwfliq/cLx6cDjSuEg8LUad1UlGChuH89bGAPOG4RI4Xd'
            b'giOsCYtUHveslD/oWwtGCAIt7bgTuKde0uxxT1k4aW/WId/3mXoOqGHY9IbJwqY7'
            b'67TewY3qO2YtCcesG6u4t+DCOnh7xDA8pvLItSyIqw5B5o7stXREC64S/Ewa50yv'
            b'TjyigEOs9VeDJ3CvU/9x+E/41WC3sFs6lqS3CtJ3ohA6qZ5Hh/CSEKHYX4NNNWG0'
            b'cBS7SZzoRa4uvCesMGfUakQ94zeLdmGzMjW5Jgg/eIxL6jiQXHuFEOZWIXr9e70V'
            b'/w+f7LsG8ir5XQAAAABJRU5ErkJggg==')
ICO_STOP = (b'iVBORw0KGgoAAAANSUhEUgAAACsAAAAwCAYAAACITIOYAAAABHNCSVQICAgIfAhk'
            b'iAAAAAlwSFlzAAAOxAAADsQBlSsOGwAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3Nj'
            b'YXBlLm9yZ5vuPBoAAAOwSURBVGiB5dlJiBxVHMfxT7dJJhqJF5NMHMUt0VHnIB7m'
            b'4pK4gYgHQRAET6IHIwgeJOACKiKKwoCIF8WDiCaiRlBRUDAkQfGk5JANlzEnhcTJ'
            b'ZDSLY6Y9vKrU65ruTnVXdbfgD4qeef1fvt393qv/+xfV6xX8iaf7ELtyHUcDv1cd'
            b'uF51QCxJXpdWHbgfsH1TP2FrVQfsB2yjDzHxP5kGa/EEtmKyoM8k3k/81vaYtyvd'
            b'hG2YF37uBnbmbE4m40dy47sin/kkzo39gLwQW6Jk6bWAJwvCPpXY5/3fxVhVoA8K'
            b'd6Q4ySFM4eoW9u1gJfZTOJyLN4cHykAuwau5oEfxOJZ38DvRATbVcmxOIOP4Uzir'
            b'W9ARfJ4L9AEuKOCbws4WsB3DR7k8n2FZUdAa3tY8r55RfJPvBjbNtxmnopzvKbhT'
            b'vRQ5zeOegklTpYVMUdhU9+KfKPeLZ3K4RfOKfaTLhGSwR3vwfUjzlLi9neEK/BwZ'
            b'vtxDMsrBEurhlOFHnNPKKP759wiLrBcdUw52BPsilhfyBuclwdMFdUOPiSgPCxtk'
            b'03EWK+M3H5N9kk9LJCGDnSsZ54uI6dH4jQPRG3eUTPKXamDvjJj2p4Pro8GflC+a'
            b'q4KtaV7w6+rYGBl8qXzxvFDSP1UDX0X/b6gLkznV9gqS7Eped1QQa3v090b4VvZV'
            b'X15BgmW4TjWn23iKfkOYp+nAigoSVKmVmm8Qp/fX40OE6qTTtUZdVpv+l2HhbJgR'
            b'yP8eGk571WTnvcN14YhCWBCrh0XVRmtk7ahDdaFoSDU+eJ6Oinn21bE7Grh+wDBn'
            b'UlxQ7YbbZNvD18Mg6qCdMrabCbvBbDJwChcPDa1Zl8rKxBmM1IUD3tbEoI6Hh8O2'
            b'SJtkRdUWoR+BcHtMP8UcVg0crVmjssbKAq7NG3wimx9vDRRtsd6JWLa1MpiQtX4W'
            b'cNfA0Jp1twz0JK5qZ/h8ZPiHUPUMUuNC2ylleLaT8VLNrclfhA7iIHQRfo1y75Dd'
            b'vdpqDAcjp2mtu4VVakIz6LQuGs5XCs+xUucjuK9yxKD7ZWVqA7/pYfqtFwreuJ3z'
            b'IS6pCPIyfJyLfwDreg24yuLW5wm8gWt6jDmBN2U7T9yvOL9X0FQ1ockQr9L0+l5Y'
            b'sbdqfyNZLdQfz+GHFjFmhAZgpc/NRvG67JjR6poTznR7hTN/vrMdX8fwmj7X0KPC'
            b'E++9HUA6XXuEhyFruk1c9qsfF87zk7hCqJTOFU6ls8L9fVpYON8JfYD9i8MU07/Y'
            b'BV0QpMnylQAAAABJRU5ErkJggg==')
ICO_WIZ = (b'iVBORw0KGgoAAAANSUhEUgAAACQAAAAwCAYAAAB5R9gVAAAABHNCSVQICAgIfAhki'
           b'AAAAAlwSFlzAAAOxAAADsQBlSsOGwAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYX'
           b'BlLm9yZ5vuPBoAAAPvSURBVFiFzdlriFVVFAfw350ma0pNJqmoiIrKL4VEQxIGQ6A'
           b'fYrKXFaUQUWGhUVBBQaDRA+pDFL2skIwe0GOU6KVl9KCSHoa97ItDD6UvFWbW1Ix2'
           b'vX1Y+8ycuc7ce+Y2905/2Nxz9t5nn/9Z67/WXudcRuIVVCaxbS5VEfoOZazReszH7'
           b'PZRBr7FrS0mA9MkQhtwWuo8BEdjxwTfrIxHsaLexHbMw1Z8McEk8rgQy4UVbhJ6qc'
           b'aQfCp4oIlk4K/UsntVaxdW4p/RNNQsPCc8cgP2w/VGWqokTWgVyliCv3EdDsC12Jv'
           b'G21pNiLDIsvS7VFjlmkSq5RY6R0S0dPMyrsZ23JH1t4pQL+bi+Fzfjzgi19ewhWZg'
           b'oRBmhh/wVo1rLh+j/w3Dwm5DZTyEzki/J+Nx7EznU9KinVgstp0/Cq7ZliNUyjqKo'
           b'AfvpnZZItOZ2jJ0iKddjfWY3kxCC7BW5JHVOAl35sbfxus4BVfgOLwptqEihDIUyt'
           b'TdGMQTVRfPxMW4CmdWjc3CT9io/gO/g1Xp+GmU62moLTEfNJwrbkvtQJHkOvCN0M9'
           b'XaW6lAJls/cIuOwwn4GORQ4gNcjnuFvqZKiqFP8XTHoNTcZTQVE8BQhnquuxGkbx+'
           b'FSn+cAwI61Rjugj9VSLqPk0ky0amh2p8KORAaLRcy0LtQgsz8RjOSjdbOcrcXXgGZ'
           b'2M3ThcCz1w+FkoaDHuilhnE72OM/6x4uGfYx2X1CE0VO/Sx2CKEPGeMud1C3ESqmF'
           b'eQ0AgLMbaGetAnLPJqungTvhR6ymOxiMJFIuz3Yhs+UNtlnxmWwAtCczXz0DR8It5'
           b'GiKjbhl/SQitEZq7goTTn/HS+pAaRDJ/nCL1YhNDSNL4o19eJu9JiW/Eazs2Nl0SU'
           b'9au/eW8WxT+8VIRQh9gGdqALs8Xe1Vk1b44oTafgYezBJXXIEO7PCPUWIUQIeR1+S'
           b'60sLJNhQVqjjO9F2F9UgAx8jUfS8RoFtg4iGV6AZ9P5RyJT35LOu0Q6mC8S46ViMy'
           b'6CfaKsaD00YPipu0XCzIv2PRFRswqulyeUoeGK8X2c2MB1o6HhAi3DDJEGunCeKNj'
           b'gPtw+AYTGXeTvEa7ZKTbNjal/iyhFGiGUoSGX9ePmdNwnrAVPNkAmI/SfXDbRyBMa'
           b'6phMjHu3bzb+1y4bVdQbxBe0ZuNePKVAlG0Xod1sZFVnXQtd2QIyedQl1IsjW0DkQ'
           b'TyvgMtKapecE4XsHnUttLAFZPKoa6G1OLQFRO7Hy0Z5L6smdBAObgGh/dPvuF6DWo'
           b'EBURb3ibff/sxCc3FPwUUqhr+eNYpdogZvF69Ym1L/euITymT9HbVb1OBD+Bdofym'
           b'p7096lQAAAABJRU5ErkJggg==')
ICO_BCKCHN = (b'iVBORw0KGgoAAAANSUhEUgAAACQAAAAxCAYAAACyGwuwAAAABHNCSVQICAgIfA'
              b'hkiAAAAAlwSFlzAAAO6wAADusBcc2BlQAAABl0RVh0U29mdHdhcmUAd3d3Lmlu'
              b'a3NjYXBlLm9yZ5vuPBoAAAXHSURBVFiFxdl7jF1VFQbw37nnzgA+KpYUqgIFrQ'
              b'9AoVAjEUOiVk18xUfFBhTFJ+CjYiQiscY0PmijkhI0FYqJmCJVIwmDIJWHVkCs'
              b'Qi2KQqu0AWsIrY/BlvJw7j3+sfade3rmvqZlpl9ysu/ss87e31l7r2+tfYY9cS'
              b'2K/XhtyCqEtqCGtaYfr8HLqp1bhJf2B76DsTp+jPmp8wgchgee5skaacJL+hnW'
              b'cRr+jk3CQ1OB12MFDsTyLjbj26dIxoPgMOHNBXgFnj3gc7uFlwqc38VmpbRk/X'
              b'AwFgtPvrxy73/4Da7A1WnSbvgBDsU3xMosq9yvtX708tAHsCPZ/BEX4Sy8B+fi'
              b'Mjyc7v8ZJ3QZZze+i4Nwc7K/oGJzOcZ6EVqe7m0Ue6Ab6oncP/E43taDEDwDt6'
              b'CJT5dsVvUi9PnUvya9VRnDOe9W2oQJL8RfEqlTOhD6g1imZbhULHcTHyoRanQi'
              b'9KrEdK14+3EMMa/GppxVtZj8kMrEh4sl/BueWeq/V3d1/n6yuQKNmolYhsfwfr'
              b'Hr31SPqNLg1Rk7mrwhkT4chnnvECdhG87Bi/CJ0pjzMLPDdVMiRfJ4NcqOxeuw'
              b'FDtyripCLGs5n8NzkWccgNE8ImZGg4cL5ta5dowlWC/2xzfThGPpJZ+Ph8RSpX'
              b'ccJ1RDUfXQO1K7JrVHpMGeLJjb4PQGp2RsaXJSjQsLDi6Yk7Gp4MT03NXp2ZZM'
              b'zMeD2Ir7cHSZRJlAldAJeAT3Jx+uLTiq4OiMR+t8uMa5BUfmLGpydsZ/cWgzvP'
              b'ujNM661K4Q0rAGw/gq5qQVqM7fUanXYUOF8eIan4ScVRn/qnNxxq4an0n9K+t7'
              b'RtasNO7j+LeIqI04Ev/AjcnuFrGZ4UqMVT3UU7kzRmvc2GRBzt1ZaM+ENyxhud'
              b'i8XxDefxDP046sqoeyKqFH8IISuyUZizLOyFlXMDNjM2Y3+QlOy/k1XlqwYjgi'
              b'k9g/hATAt7AQXxcR29qj5T2UVRnCXSLfHCss34qhdA03+MgYSzP+1OTbDd5ZML'
              b'OI6Huq0Sb02tT+vjT2Nfgiflnq60toJLVnpPa+ggMLDiqYlXNmzm1o5vwi56NC'
              b'AJ+FehYEMpwuomkDFuFOXK8dhWVCLXQtP27FTsyGOgvqoU0zcu6ocW+Ne2pszS'
              b'O8h4ZZONSebGEaczXOFJrzEEbFEpZT0Z0iCuGHuqSO+UJ7bhVLNY46p+asr/FA'
              b'LXLT7Mobz8F2E9PDK3Fe+n18yX69dtIdL186JdcLUv819sxJcEg9km816b5EVJ'
              b'078TFRP31KeOivIiK3i2zfwu9KhNb0IkTUPq06580d7rcwjM/iP9hlYqnyQVFL'
              b'rcPJlXt3iUqRENVGL925ULzZ93CDCPcRcQAYFeXsPLxdZP31oqDbXBnnynR1wo'
              b'Qo61fC3pTa20T9XK2HHxM6tFJEUdPkMCHKOpUfnTAiomgGvpb63pj+fguu2wsy'
              b'rfl76lAZQ0LI4H2YKzZsS33LZcTeYlIeWoyzxXK9GFft4+TdCA3soePxhKgOR9'
              b'LfnRLoIDhApJd9InSzOGluFfLfOr7sDZmf4naR6auEWuhLaLUQtvuFeJ0lxO/j'
              b'6f5X7Cly3fAl/DyRuqgDobKHMiZ3lL5DVIg/S899ecDnThZntyq2aH+AGEFz0L'
              b'Bv4RhRPrxLRNwxPWxPFOmjiuO0y5QJSzbI2b6MG4QEbBdCeX0P2+doJ9/NopQl'
              b'vhXMKhGalFJXcY4oQ48TYri6h+1GUYufWukf1ta3ctTuFaFdpcH6YVTnJSujr4'
              b'dmIB+U3T5gN54chNA9OGoaCJ0vCv++m/pScWyZavw2tX09dPE0kCmjL6GNoi6e'
              b'aiwRX2X7LtmvxLlsqrE1tRM+NlQJnTcNZMrou2S3mx4PLRX1Vd8l2ya+WEw1dq'
              b'Z2goeYXLZ/uvGEcMA2IZa7Wh5aoH2kJUqMXh/Be6GJRwe0rYvIvjs9dx2hzvvr'
              b'/2NPiWp0HP8H/X3IP8fWnS8AAAAASUVORK5CYII=')
ICO_CBCHK = (b'iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAABHNCSVQICAgIfAh'
             b'kiAAAAAlwSFlzAAAAygAAAMoBawMUsgAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3'
             b'NjYXBlLm9yZ5vuPBoAAABsSURBVEiJ7dahEYNQFETRQ1RaIPGpgxZphYCnjjTyc'
             b'T+CLxgG+XBvZ9beK3fhjQUFNagFM14aPAp87tw12xM/rGIy4IPNwTYGwTVWRX0E'
             b'Qi+TghSkIAUpSAHcPZmFff3vGv2J/Vp8xd+WCf0fuZVmwe+b7gsAAAAASUVORK5'
             b'CYII=')
ICO_CBNCHK = (b'iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAABHNCSVQICAgIfA'
              b'hkiAAAAAlwSFlzAAAAxwAAAMcBYjN5IQAAABl0RVh0U29mdHdhcmUAd3d3Lmlu'
              b'a3NjYXBlLm9yZ5vuPBoAAAEoSURBVEiJ1daxLgRBGMDxH1Hc4QXwChqVRCtatY'
              b'I3UEiIoLhGo5MrNJKrPIFzGkKCxBN4EQWrW8XuyRq7t3cyV9yXTPN9k/9/dne+'
              b'nYEl3CJBGmkk6GFRDo8FDkdvKrc18IZXcWINy/hSsLUjweWsFOl0RGhpTISgiS'
              b'vslhVnIsCvsYFt2YbpxBLMoov1Qq4RTvrvKyqDt3AxrGAFOxW1OVlzFuHHOK1a'
              b'TdgHq3jPcyfB3Hk8+d2thyXMdqH+R3AeAI4K8OegdlCx6IGCJu4CUAsvQW6/Al'
              b'4r6EvuA2DZU9UKqj5ygk08BPkUezirEfzEoG3alzwG8JF+inWN9plLOrnochT4'
              b'MAL4wNao4H5MxN90YIz7yEzITv9xHfpdsqvFjfjXli4WvgFlkbAzkqReWwAAAA'
              b'BJRU5ErkJggg=')
ICO_INFO = (b'iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAABHNCSVQICAgIfAhk'
            b'iAAAAAlwSFlzAAAAsQAAALEBxi1JjQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3Nj'
            b'YXBlLm9yZ5vuPBoAAAG6SURBVEiJrdY9axRBGAfwX5IzvmFSCB42YqFJIWiMpYpY'
            b'xEawsRP0C1iK2NhY2KQRtAkJaWxFYlJYqPVFP4CF2CdYiG8gd8ihxe7CZG5mdw/8'
            b'wwO7M/P8n9d5mdCMWSxhHt1y7As+4Q1+tuBIYhFbGOBvRgbYxMI4xAexjmENcSxD'
            b'rOJAE3kXH8YgjmUbx+o8z5F/xAPcwBXcUaQvFeV2LpL1xOI/uIeJjFOXsJPQW40X'
            b'Lma8uZsLN8AZ/I70hqLCbyXIP0dEJ/AQj3A6mnuS0H9VTc7Kt+JzHMYpe1PxA0cD'
            b'A9cTun3MdHAN05nwb+MyDtnbHYNoXapG+7E0mQg3xsmI/AXO4mswdjWjOwfPtOvx'
            b'Pm4mSC4aLXIlTycbvA/xGC+D/324j3eKPZREB7stDbwOvqfRw4UGnZ2O0XbM4VZA'
            b'ON+CXMVd16axfC+lbc2OVJY2WygsY6qU5RbrN8JQzqs/nr+VxBWmGiIZ4lycr7WG'
            b'1IxjYCUmpzhi3/+HFPUUuziJboORpiL31Fw4YSRrxr8yV+o8T2FBceT2a4j7im4Z'
            b'KWiF3E0VYkbxbJnD8XJsV/FseYtfdcr/ANVRC3ZXH1BbAAAAAElFTkSuQmCC')
ICO_ABOUT = (b'iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAABHNCSVQICAgIfAh'
             b'kiAAAAAlwSFlzAAAA7AAAAOwBeShxvQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3'
             b'NjYXBlLm9yZ5vuPBoAAAHfSURBVFiFxdfLThRBFAbgj4YV6LBRZO114cbrK5j4A'
             b'KIm7kh8BTND4pqFT+DCLfo0jpeYiANBTIwxLhC8bHRwUV2ZsZmhu3qa8Ccn6VT6'
             b'nP+vrjpVf09JxyKu4AJm87Gf6KGLLzVqlmIBK3iD/ZJ4jQ5ON0E8h0fYqUBcjB9'
             b'YRasu+U18qkFcjG3cSCW/I6zrpOQxfuNBVfJ76DdIHqOPu2Xk1xqeeTF+CUs7Ei'
             b'ekrfkHtPPoJeR9NGjf//A4och6LjjiZKKIlSL5AnYTCrRHTKCTkP9dfk5kefLDf'
             b'BaTYCrh3RaWhwfejlE6LnoFwS1sJNboRtWL+Jw4Aznhs/x5GWcT8/dzbrcTlTcZ'
             b't7IaytcwI3yxGJcTa0SczzCfmLSOv4WxdzUFzGfl7xzARUzXJDyATOjJFNzHn4b'
             b'4dzJsNlSsDjYIrVDn9isiNb8vnMCoZrWaFvCSwVG8VvKphhHbsIgZPE+o82JYwF'
             b'PhMqqCUW0oH3tfscae/BSNAr7hScXkcW04jUsVa6zia3FwTjCQR338bhljSOCqY'
             b'7RkEUdpSpfKyCOO1ZZHXNfMntgS3HYtzKr/a7Yn7PZJrR6CgezglcP3R1+wWm2c'
             b'qlI41YbBGeH3/JzB7HaFi6VrRH8fhn9QlcxM55dRyAAAAABJRU5ErkJggg==')
ICO_C_S = (b'iVBORw0KGgoAAAANSUhEUgAAAA8AAAAYCAYAAAAlBadpAAAABHNCSVQICAgIfAhki'
           b'AAAAAlwSFlzAAAAsQAAALEBxi1JjQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYX'
           b'BlLm9yZ5vuPBoAAABbSURBVDiN7c0xCoRAEAXRh55NkF1QD+5pFHbVRKNJZJCezGA'
           b'KOuig6lOpBOjxx1lwP3QNFrSFgy3W9HywBVd3TPdaJHDkxEjgUUx8M4GQmAsUiYkR'
           b'M4ZSsfI6LsddNmrLM3dAAAAAAElFTkSuQmCC')
ICO_C_S = (b'iVBORw0KGgoAAAANSUhEUgAAABAAAAAJCAYAAAA7KqwyAAAABHNCSVQICAgIfAhki'
           b'AAAAAlwSFlzAAAOxAAADsQBlSsOGwAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYX'
           b'BlLm9yZ5vuPBoAAABoSURBVCiRndBNCsJADIbhB08hWgfb+y/tNXRVF/2h9SS6sTC'
           b'UwanzQUI275sQaPEurNsBQXnC2qaC7S80sWn8A15Qb8+57JQk4Vgy/IBnXHOPOeKZ'
           b'gHtUOTiWdBv4vBdec8ID9++czAfA00bxUzJkbAAAAABJRU5ErkJggg==')
ICO_C_H = (b'iVBORw0KGgoAAAANSUhEUgAAABAAAAAJCAYAAAA7KqwyAAAABHNCSVQICAgIfAhki'
           b'AAAAAlwSFlzAAAOxAAADsQBlSsOGwAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYX'
           b'BlLm9yZ5vuPBoAAABiSURBVCiRnc9LCoAgFEbhQ6sIe1DtfzFRNOlBtpKa3AtCaua'
           b'FM/P7QQifAUbJRN55rwQW4JZWoErFNbA5WDuB7gs3AeyO9DG8R7BmfSNtItYuYHDx'
           b'8QO/RuYMrE2F/Cn37APQL0jJONheYAAAAABJRU5ErkJggg==')
ICO_ADD = (b'iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAABHNCSVQICAgIfAhki'
           b'AAAAAlwSFlzAAAOxAAADsQBlSsOGwAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYX'
           b'BlLm9yZ5vuPBoAAAD6SURBVFiF7dcxTsNAEIXhLxY5ANBAQZkKCijIMUBCAe5JkVs'
           b'QKMIJKFIBfVxAYQsh4iVhlHibfdI2s96ZXx57ZodGd3hCjc8dr7qNNWlju+8haGrd'
           b'wnNGgNkASwzlUT1oSbJpL3hugZdftlMcR5xFcjfu8DOO+KoixPjY0LZWUYCtqQAUg'
           b'FQhWuAK74lzr5qm8lNDnCSeP8CDRJ3o+j+nf1EHNe2KlT0FBSDVjM5xibfE/n8/wk'
           b'NcpCAizWjU4WcU8ZU9BQWgAEQB9je0rVX0Vtx1KT3DUV8AW1NltaL1qbqy+ir71By'
           b'u5ZsNvyfkCWaaOXHXQZd4xA18AUBs7RVVzKvVAAAAAElFTkSuQmCC')
ICO_ADD_S = (b'iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAABHNCSVQICAgIfAh'
             b'kiAAAAAlwSFlzAAALEwAACxMBAJqcGAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3'
             b'NjYXBlLm9yZ5vuPBoAAADTSURBVEiJ7ZYxDsIwEAQngQIKEG0gBX/hCyglj+MJE'
             b'Dr4SCqkFLRIFE4HRSwhjisOYoOQWMlFTt7d2OtcDDADdoADroGGA0pgihcPJSxH'
             b'mXi3AXHQJN4pGvrGeQ5YAWf/PAHWwNBCtuxlpfAqCzc1ruBt/L6BFrIDTqJWK/N'
             b'qoCdqGUrwMpji5de8o5B62hZdOhg8cb8S8qiD3lgWtFahhXwEFqJ2AOaiZgr5/y'
             b'V/1sDarnNgyWO7zi3E6D+cFGgi6ruU9jzHwh7aq8WW8NeWDZDdAPNsiQJFJgbeA'
             b'AAAAElFTkSuQmCC')
ICO_EDIT = (b'iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAABHNCSVQICAgIfAhk'
            b'iAAAAAlwSFlzAAALEwAACxMBAJqcGAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3Nj'
            b'YXBlLm9yZ5vuPBoAAAC9SURBVEiJ7dAxagJBFAbgr7CIR9hbxDN4BAubiCfwDNlK'
            b'PIedR0iKHMLWQiEKQbSzFS3cCYuwUXdnCiEPHgMD8/3DT5wZYYsVepHM38lxKu0R'
            b'w1R41JAM+4qAEFK7rje8oHMjZFkHz4vHH3eE/NTFw94KGTXBw36ijVfsSvfvMfCq'
            b'kElM/LquLAUedpASj9r5P/5keP9BPH8Eh3Gqn4eZpsThKyUOi5Q4HP7A86Z4y6Wi'
            b'LtbYFOc35pg1DTgDrYjjYwmLHkgAAAAASUVORK5CYII=')
ICO_REM = (b'iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAABHNCSVQICAgIfAhki'
           b'AAAAAlwSFlzAAALEwAACxMBAJqcGAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYX'
           b'BlLm9yZ5vuPBoAAADvSURBVEiJtZZRDsIgDIY/fTBeZC7xxOIp9EUP4PQkLvFVPQA'
           b'+0C0Lga3FrUmfKN8PpVAg2AY4Ah/gDlTYrQIewnDC7OFnwA/8BeyN8GfEuAJbZOU+'
           b'4S2wU8B3EptiOIBvZlAjMgb3wBtCznMBnUidgNcTcA/cIORvKjAW0cBbBsWSOqTYu'
           b'4OfSku2SDQTW2VM9tw0OzGvfC4R092xilgvpklkFL4eEViJL2KaiipOkRVurqASuE'
           b'pk0YtmeSosseq0/PXYLflcNxB6qCmfA1M1HFcI14gcIDT9UzQwR9O/IE2/E3GypYb'
           b'yb0sjjP7b8gPYMEUyhPJmHgAAAABJRU5ErkJggg==')
ICO = (b'iVBORw0KGgoAAAANSUhEUgAAABgAAAAfCAYAAAD9cg1AAAAABHNCSVQICAgIfAhkiAAAA'
       b'AlwSFlzAAAOfgAADn4BMFB4OgAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5'
       b'vuPBoAAAbcSURBVEiJrZZrcFTlGcd/Z8/uOXvJbjaXTVhMNhcIYLiEAAIBrNByqWVEq9V'
       b'AW6m0Q1vjWNv6wU5bZtopbR2ZVmEqthRQqYByMVbGYsAIBCRgyA1SwoaEQCABsiTZzd73'
       b'nD2nH2wiIGo78P9yZt5zzu//Pu/zPO/7Cny58o2StEKSLYsVJVEg6IJR01RRNBoHRdFUG'
       b'wkF3gIqAeVWPwtfAPbIZttGkyzNGH/PXEve2ImmNJcbo0kCIBIa5EpXB97G2mB3Z2tcU5'
       b'XfKIqyHtC/1EAUxXKjbP7b7PvL7XeXzjIgCAQHruHr6SIc9GMQRZyZI8i6Kx+TJBMKDHD'
       b'gndfDvZc6m2OR0EOAb5h1M9xkMlVY7c61j1WsSh2ZP0Y47z1JzZ6tdLY24HSlkVs0GqNJ'
       b'oLvzDAcqtxAaHMDtGc2EGXMlUTSO6L3UWa6qyhYgBmC8iT9bsth+/2jFKodJMnOg8lV0X'
       b'eUXr7zO6Emln4k0Ehxk79bN7Fr/J8oWfouS2QtMgiDkfPzhP6vj0cg0QLs+Aotstny0eP'
       b'lPM1PTXFS99QrF02fy641vkjHCfcskmWSZ4mkzmf2NB/nHmlXY7GmMLS0TL3e1p4YD/oC'
       b'mJT82fLo08sqCu0tTsnMKaDq6j9yiMTy5+s8IwhfVwSdy5xXy/K4qjlbtIBIMMHfJcqtg'
       b'MPwOkIcjMErS7vmPrcwEOLxnK3/csReTLAOgaxp1H+yl/tB+2ppO4G2sw9tYhzPTRUqqE'
       b'wC7M42ELtJUU8Wo8VO51nM+2d/X2zYUgUc2W23OjGy8TbXMf/Q7WO0OADpamtnxlzXYHK'
       b'm4FD/3Cj3MEHw47XbamurZ/dcXUZUEAPO/vYLz3pMoiTjjpsyxWS0pK4YMyu4qGKsD9F4'
       b'6x/QFiwFoOf4RXWdbeeTJn5M88R4Xe6+xJuRm4zWZvMsNGNQEi5Y+wZtrn0dVFKxWG3kT'
       b'p+LruUCmOxdNS04YMsiwO9MtAIF+H7lFY4lFwrSfbGDeN5fibaxDDw1SP6ihnq6nbe7jb'
       b'LmoUBBoI8WZxgPfr6Bq22aUpIYrv4hAXy82RxqqkkgbMpANRpMBQNOSGE0mBnxXSc3IBC'
       b'AaChJRVHrKn8M4bgruynUkRBlZ1wBIcTgJ+geIqjpcVxSCIDBk0O3vuxoFcGZk0dPZgTu'
       b'vECUe54L3NOOmziDf5WTCnrUkZQvCCA/znElakp/k6Z2/r2N++XIG40n8ly9isztREnHA'
       b'EBsyOO3ruaACZGTn0nBwPwALlz1BW9MJGmuq6Zt0P8vcUO5v4Ie0I9udjFv0CNtf+gNlX'
       b'1+C7nChJlU66o+S7SnkysUOJIu5Zdgg2N9HeNBPUclM/vXGpuHKWFC+nILiiXibG2g05t'
       b'CspXFcz8InZXCq9jAP//hnpOYUci2icnL/u7g9o5DNVjpbm2LRYGDX8IKZZMuLk2cv/NH'
       b'0ry2xHK3ayajSqaz85W8/01S6rt/QfMF4ku5gglDAz0vlX+GrD34PR3omW154LhiPhT3D'
       b'jaYl1XpfT9dTY0pmmj2jx1O9czMxo5WC8SVI4o2JA4gqGlfDCr6ISjQU5NWnl1I4poT8c'
       b'SUc/6Ay5rt8YXNSVSqv34sigkHo6z7XOmf8PfdZCsZOZt8bL3Om5RT2oikookQwoTEQU+'
       b'kNq/RHVeJJnfa6w7z2zDI8hcVMnDmPi2db9GP73u6NxyIPAcpnNhqTbN6QnVOwdPHjP7E'
       b'bDCLNx6ppaz5GQekM8qfMwpqaDkBvp5eW6j0Ims70eUvIzi3kUkervnf7en8iGpkFnIFb'
       b'HziCaJLXpdgdP1i0rMLiGulB0zS62k7h7+8lGg5ikiQsVjvuvCLSs0aiaRr1h95LNB+p6'
       b'ovHoguAfw/DbmHgsjnSm8zZhSMjV8/hGjEyUVK2QHLnF2GS5Bs+HOz3IVksie72M+8ffH'
       b'fLQCwSfgYI3DDbm+AOm8PZNm3eA9l5E2dxsuUU3uptfl1L1qqJ+L2yxaqYJNmga3oyEgp'
       b'YRNF41Sibnw35+96+xUSBm0402ZayW1WVbAGBFNmILdEHaJtj4eCzAKqScALZQBTwKcSj'
       b'RMOfx75Roig+7PIUBpav3qCPmTpHz3Tn6plujwrc978RPof736ckmS0fLq74Vbozy82oK'
       b'WVIFhvtDUf8qqI8dTsGRoCKl3ek+7rOy+nu3OEXp2reH1Tisae56Z7z/8oAlB7avqkqK2'
       b'+0Y2jwbF2N5r9y6XQymdx2O3AAg8Xu2FA4efqkoYF4JETNzk2hWCT03duFAxiUeLzYU/z'
       b'pnefIrtfCmppcC3TcEQPRJJ/xHjuoAbQ31Oqdzcd8iVhk9Z2ADylHtqXUGyU5ZLE5GoGC'
       b'Own/D8Bg1KvOieQ0AAAAAElFTkSuQmCC')
ICO_M = (b'iVBORw0KGgoAAAANSUhEUgAAABgAAAAfCAYAAAD9cg1AAAAABHNCSVQICAgIfAhkiAA'
         b'AAAlwSFlzAAAOdQAADnUBuWNRMgAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm'
         b'9yZ5vuPBoAAAcDSURBVEiJpZZ7cFTVHcc/d3fvvdnd7GbzzmKyeUAAwyMEEAhghZZHL'
         b'SNaKQbaSqUd2hrH2tY/7LRlpp3S1pGxClOxpYBK5SGvWBmLASMQkIAhL0gJGxICgQTI'
         b'kmQ3+957997+gYmAKLX8/rlz5pz7+f5+5/f7nXME7m55JklaLsnmBYoSyxd0waRpqtF'
         b'oMg0YjWJNKOB7B6gAlDv9LHwJ2CUnWDeIsjR1zAOzzLmjxonJ6U5MogRAKDDA1c523A'
         b'01/q6OlqimKr9TFGUdoN9VwGg0lpnkhL/PeLjMdn/JdAOCgL//Op7uToJ+LwajEUdaF'
         b'hn35SFKMgFfPwfffSvYc7mjKRIKPAZ4hli3w0VRLLfYHGueKF+ZNCxvpHDBfYrqvVvo'
         b'aKnHkZ5MTuEITKJAV8dZDlZsJjDQj9M1grFTZ0lGoymr53JHmaoqm4EIgOk2/gzJbP3'
         b'j4vKVdlFK4GDFG+i6yq9ef4sR40s+F2nIP8C+LZvYte5lSud9h+IZc0VBELI/+ehfVd'
         b'FwaDKg3RyBWU4wf7xg2c/TkpLTqXzndYqmTOO3G7aTmuW8Y5JEWaZo8jRmfOtR/rl6J'
         b'VZbMqNKSo1XOtuSgj6vT9Pinxg+2xp5Rf79JYmZ2fk0HttPTuFInl71FwThy+rghjlz'
         b'C3hxVyXHKncQ8vuYtXCZRTAY/gDIQxGYJGn3nCdWpAEc2buFP+/YhyjLAOiaRu2H+6g'
         b'7fIDWxpO4G2pxN9TiSEsnMckBgM2RTEw30lhdyfAxk7jefSHe19vTOhiBS06wWB2pmb'
         b'gba5iz+HtYbHYA2pub2PHX1VjtSaQrXh4UupkqeHDYbLQ21rH7b6+gKjEA5nx3ORfcp'
         b'1BiUUZPnGm1mBOXDwqU3pc/SgfouXyeKXMXANB84mM6z7Ww6OlfEj/5Ppd6rrM64GTD'
         b'dZncK/UY1BjzlzzF9jUvoioKFouV3HGT8HRfJM2Zg6bFxw4KpNocKWYAX5+HnMJRREJ'
         b'B2k7VM/vbS3A31KIHBqgb0FDP1NE660k2X1LI97WS6EjmkR+WU7l1E0pcIz2vEF9vD1'
         b'Z7MqoSSx4UkA0m0QCgaXFMoki/5xpJqWkAhAN+QopKd9kLmEZPxFmxlphRRtY1ABLtD'
         b'vzefsKqDjcVhSAIDAp0eXuvhQEcqRl0d7TjzC1AiUa56D7D6ElTyUt3MHbvGuKyGSHL'
         b'xWxHnOb4jTy9+4+1zClbxkA0jvfKJaw2B0osChgigwJnPN0XVYDUzBzqDx0AYN7Sp2h'
         b'tPElDdRW94x9mqRPKvPX8mDZkm4PR8xex7dU/UfrNhej2dNS4SnvdMTJdBVy91I5kTm'
         b'geEvD39RIc8FJYPI1/v71xqDLmli0jv2gc7qZ6GkzZNGnJnNAz8EipnK45wuM//QVJ2'
         b'QVcD6mcOvAeTtdw5AQLHS2NkbDft2tow0TZ/MqEGfN+MuUbC83HKncyvGQSK379+881'
         b'la7rtzSfPxqnyx8j4PPyatnX+PqjP8Ceksbml17wRyNB11CjaXG1ztPd+czI4mkJrhF'
         b'jqNq5iYjJQv6YYiTjrYkDCCsa14IKnpBKOODnjWeXUDCymLzRxZz4sCLiuXJxU1xVKm'
         b'4+i0KCQejtOt8yc8wDD5nzR01g/9uvcbb5NLbCiShGCX9Moz+i0hNU6QurROM6bbVHe'
         b'PO5pbgKihg3bTaXzjXrx/fv6YlGQo8ByucOGlFOWJ+Znb9kwZM/sxkMRpqOV9HadJz8'
         b'kqnkTZyOJSkFgJ4ON81VexE0nSmzF5KZU8Dl9hZ937Z13lg4NB04C3e+cASjKK9NtNl'
         b'/NH9puTl9mAtN0+hsPY23r4dw0I8oSZgtNpy5haRkDEPTNOoOvx9rOlrZG42E5wL/GY'
         b'LdQSDdak9pTMgsGBa6dp70rGGx4tK5kjOvEFGSb1k40OdBMptjXW1nPzj03ub+SCj4H'
         b'OC7xdvb4Har3dE6efYjmbnjpnOq+TTuqq1eXYvXqLHog7LZooiSbNA1PR4K+MxGo+ma'
         b'SU54PuDt3XMHR4HbbjTZmrhbVZVMAYFE2YQ11gtomyJB//MAqhJzAJlAGPAoRMOEg1/'
         b'EvtWMRuPj6a4C37JV6/WRk2bqac4cPc3pUoGH/jfCF3A//UpSgvmjBeW/SXFkOBk+sR'
         b'TJbKWt/qhXVZRn7kXABFD+2o4UT+cFOcWZMzRxuvqDASUaeZbb3jl3MRE4BiwG4sAeA'
         b'1ByeNvGyozcEfbBVedqqzXv1ctn4vH41q/osPApeBFQBsRNZpt9fcGEKeMHV0RDAap3'
         b'bgxEQoHvf0X4oF0FsrixO10mJRotchV99uY5uuvNoKbG1wDt/6cAQB038usyGEX5rPv'
         b'4IQ2grb5G72g67olFQqvuAQ6wHdgyOMiWrYl1JkkOmK32BiD/HsAi8PJN49X/Bb0p32'
         b'Bilx0IAAAAAElFTkSuQmCC')
ICO_I = (b'iVBORw0KGgoAAAANSUhEUgAAABgAAAAfCAYAAAD9cg1AAAAABHNCSVQICAgIfAhkiAA'
         b'AAAlwSFlzAAAOfgAADn4BMFB4OgAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm'
         b'9yZ5vuPBoAAAbuSURBVEiJrZZpdFTlGcd/d+7MvbNkJpNlEgbJZIEAhiUEEAhghZall'
         b'iNarQZapNIe2hqPta0f7GnLOe2prR45rcKp2FJApQLKYqwciwEjEJCAIRukhISEQEIC'
         b'ZLLMZPa5d+7tB5rI5nLU/5f74X3v7/887/O8i8DnK8coSask2bJEUeK5gi4YNU0VRaN'
         b'xUBRNVeGg/y2gDFBu97PwGWCPbLZtMsnSzAl3zbNkj5tkSnG5MZokAMLBQa50tNFcVx'
         b'Xoam+Kaarye0VRNgD65xqIolhilM3/mHNvif3OotkGBIHAQC/e7g5CAR8GUcSZPoKMO'
         b'3IwSTJB/wAH33k91HOpvSEaDj4AeIdZN8NNJlOp1e5c90jpmuSROWOFC82nqNy7jfam'
         b'WpyuFLLyx2A0CXS1n+Vg2VaCgwO4PWOYOHOeJIrGET2X2ktUVdkKRAGMN/HnSBbbnx4'
         b'uXeMwSWYOlr2Krqv8+pXXGTO56JZMw4FB9m3bwu4Nf6F40fconLPQJAjCqI8//HdFLB'
         b'KeDmjXZ2CRzZaPlqz8RXpyiovyt16hYMYsfrfpTdJGuG9bJJMsUzB9FnO+cz//WrsGm'
         b'z2FcUXF4uWO1uSQ3+fXtMTHhk+WRl6de2dRUuaoXOqP7ScrfyyPP/tXBOGz+uCa3Nl5'
         b'PL+7nGPlOwkH/MxbutIqGAx/BOThDIyStGfBI6vTAY7s3cZzO/dhkmUAdE2j+oN91Bw'
         b'+QEv9SZrrqmmuq8aZ7iIp2QmA3ZlCXBepryxn9IRp9HZfSPT39bQMZeCRzVabMy2T5v'
         b'oqFjz8A6x2BwBtjQ3s/NtabI5kXIqPu4VuZgpenHY7LfU17Pn7i6hKHIAF31/FheZTK'
         b'PEY46fOtVktSauGDIrvyB2nA/RcOs+MhUsAaDzxER3nmnjo8V+ROPkenT29rA262dQr'
         b'k325FoMaZ/Gyx3hz3fOoioLVaiN70jS83RdJd2ehaYmJQwZpdmeqBcDf7yUrfxzRcIj'
         b'WU7XM/+4ymuuq0YOD1AxqqGdqaJn3KFs7FXL9LSQ5U7jvR6WUb9+CktBw5eTj7+vB5k'
         b'hBVeIpQwaywWgyAGhaAqPJxID3Kslp6QBEggHCikp3yTMYx0/FXbaeuCgj6xoASQ4nA'
         b'd8AEVWH65pCEASGDLp8fVcjAM60DLrb23Bn56HEYlxsPsP4aTPJcTmZuHcdCdmCMMLD'
         b'fGeCxsS1Or3zz/UsKFnJYCyB73InNrsTJR4DDNEhgzPe7osqQFpmFrWHDgCwaPljtNS'
         b'fpK6ygr7J97LcDSW+Wn5CK7LdyfjFD7HjpT9T/O2l6A4XakKlreYYmZ48rnS2IVnMjc'
         b'MGgf4+QoM+8gtn8Z83Ng93xsKSleQWTKK5oZY64ygatBRO6Bl4pTROVx3hwZ/9kuRRe'
         b'fSGVU4deBe3ZzSy2Up7U300EvDvHl4wk2x5ccqcRT+d8a2llmPluxhdNI3Vv/nDLZtK'
         b'1/UbNl8glqArECfo9/FSyTf45v0/xJGaztYXngnEoiHP8EbTEmqNt7vjibGFs8yeMRO'
         b'o2LWFqNFK7oRCJPHGwgFEFI2rIQVvWCUSDPDqk8vIG1tIzvhCTnxQFvVevrgloSpl15'
         b'9FYcEg9HWdb5o74a57LLnjprD/jZc523gae/5UFFEiENcYiKr0hFT6IyqxhE5r9RFee'
         b'2o5nrwCJs2aT+e5Rv34/rd7YtHwA4Byy0Fjks0bM0flLlvy6M/tBoNIw/EKWhqOk1s0'
         b'k5yps7EmpwLQ095MY8VeBE1nxvylZGblcamtSd+3Y4MvHgnPBs7C7S8cQTTJ65Psjh8'
         b'vXl5qcY30oGkaHS2n8fX3EAkFMEkSFqsdd3Y+qRkj0TSNmsPvxRuOlvfFopGFwH+HYb'
         b'cxcNkcqfXmzLyR4avncY0YGS8sXii5c/IxSfINEwf7vUgWS7yr9ez7h97dOhANh54C/'
         b'DdEexPcYXM4W6bPvy8ze9JsTjWeprliu0/XElVqPHa3bLEqJkk26JqeCAf9FlE0XjXK'
         b'5qeDvr63bxMocNONJtuS9qiqkikgkCQbscX7AG1LNBR4GkBV4k4gE4gAXoVYhEjo09g'
         b'3ShTFB12ePP/KZzfqY6fN1dPdWXq626MC93wxwqdw//+VJLPlwyWlv011ZrgZPbUYyW'
         b'KjtfaoT1WUJ76KgRGg9OWdqd6OC3KqO2t44HTl+4NKLPokN71zvoCygOe4Vl/dABQd3'
         b'rG5PCN7jGNoxrnqSs135dKZRCKx/UsE3QmsAEYDKwwWu2Nj3pQZk4dGY+Eglbs2B6Ph'
         b'4IovAb9FBiUWK/AUfPLmObr7tZCmJtYBbV+LgWiSzzYfP6QBtNZW6e0Nx73xaPjZrwM'
         b'+pFGyLanGKMlBi81RB+R+RV4WsA3oBbb9D6P32mCOz7+FAAAAAElFTkSuQmCC')
ICO_W = (b'iVBORw0KGgoAAAANSUhEUgAAABgAAAAfCAYAAAD9cg1AAAAABHNCSVQICAgIfAhkiAA'
         b'AAAlwSFlzAAAOdQAADnUBuWNRMgAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm'
         b'9yZ5vuPBoAAAcISURBVEiJpZZ5cJT1Gcc/7+6+++6R3WxuNiabA0IwHCEECQGs0HLUM'
         b'qLFaqCtVNqhrWGsbfnDTltm2iltnTKtwlRsKaBSDuUwKmMxYAQCEjDkgpSQkBAIJEA2'
         b'x2723vfd9+0fkAiIUvX555133uf9fp7rdwjc27INRuNyo2ReKMvRHEETDKqq6PUGw5B'
         b'eL9YE/d43gQpAvtvPwucIuySTdZMoGUvGPzDbnJU/UUxIcWIQjQAE/UNc6+qgtaHG19'
         b'3ZElEV+XeyLG8AtHsC9Hp9mUEy/XPmw2W2+4tm6BAEfIN9uHu6CPg86PR6HMmjSL0vG'
         b'9Eo4fcOcujt1wO9VzqbwkH/Y4B7ROtOcVEUyy02x7ony1fHp2ePFS62nqZ633Y6W+px'
         b'pCSQmTcGgyjQ3XmOQxVb8Q8N4nSNYULJbKNebxjVe6WzTFHkrUAYwHCH/kyj2frHJ8p'
         b'X20WjiUMVr6JpCr965XXGTCr6VKZB3xD7t29hz4a/Ujr/OxTOnCcKgpDx8YfvVEVCwa'
         b'mAemsGZslk/mjhsp8nxyekUPnmKxRMm85vN71B0ijnXZskShIFU6cz81uP8u+1q7HaE'
         b'sgvKtVf7WqPD3g9XlWNfaz7pDTSipz7i+LSMnJoPH6AzLyxPLPmbwjC583BDXNm5fLC'
         b'nkqOV+4i6PMye9Eyi6DT/QGQRjIwGI175z65Ihng6L7t/HnXfkRJAkBTVWo/2E/dkYO'
         b'0NZ6itaGW1oZaHMkpxMU7ALA5EohqehqrKxk9vpi+nouxgf7etuEMXJLJYnUkpdHaWM'
         b'PcJ76HxWYHoKO5iV1/X4vVHk+K7OFBoYcSwY3DZqOtsY69/3gRRY4CMPe7y7nYeho5G'
         b'mHclFlWizlu+TCg9L6cfA2g98oFps1bCEDzyY/oOt/C48/8ktip97jc28dav5NNfRJZ'
         b'V+vRKVEWLHmaN9a9gCLLWCxWsiYW4+65RLIzE1WNTRgGJNkciWYA74CbzLx8wsEA7af'
         b'rmfPtJbQ21KL5h6gbUlHO1tE2+ym2XpbJ8bYR50jgkR+WU7ljC3JMJSU7D29/L1Z7Ao'
         b'ocTRgGSDqDqANQ1RgGUWTQfZ34pGQAQn4fQVmhp+x5DOOm4KxYT1QvIWkqAHF2Bz7PI'
         b'CFFg1uGQhAEhgHdnv7rIQBHUio9nR04s3KRIxEutZ5lXHEJ2SkOJuxbR0wyI4xyMccR'
         b'ozl2o09v/2s9c8uWMRSJ4bl6GavNgRyNALrwMOCsu+eSApCUlkn94YMAzF/6NG2Np2i'
         b'orqJ/0sMsdUKZp54f045kczBuwePsfOlPlH5zEZo9BSWm0FF3nDRXLtcud2A0m5pHAL'
         b'6BfgJDHvIKp/OfbZtHJmNe2TJyCibS2lRPgyGDJjWBk1oqbmMSZ2qOsvinvyA+I5e+o'
         b'MLpg+/idI1GMlnobGkMh3zePSMFEyXzi5Nnzv/JtG8sMh+v3M3oomJW/Pr3n1pUmqbd'
         b'tvh8kRjdvih+r4eXyr7G1x/9AfbEZLb+5XlfJBxwjSw0NabUuXu6Vo4tnG5yjRlP1e4'
         b'thA0WcsYXYtTf3jiAkKxyPSDjDiqE/D5efXYJuWMLyR5XyMkPKsLuq5e2xBS54ta9KC'
         b'johP7uCy2zxj/wkDknfzIHtr3MueYz2PKmIOuN+KIqg2GF3oDCQEghEtNorz3Ka88tx'
         b'ZVbwMTpc7h8vlk7ceCt3kg4+Bggf2qjESXTxrSMnCULn/qZTafT03SiiramE+QUlZA9'
         b'ZQaW+EQAejtbaa7ah6BqTJuziLTMXK50tGj7d27wREPBGcA5uPuBI+hFaX2czf6jBUv'
         b'LzSnpLlRVpavtDJ6BXkIBH6LRiNliw5mVR2JqOqqqUnfkvWjTscr+SDg0D/jviNhdAC'
         b'lWe2KjKS03PXj9Aimj0qOFpfOMzuw8RKN0m+PQgBuj2Rztbj/3/uF3tw6Gg4HnAO9t0'
         b'd4hbrfaHW1T5zySljVxBqebz9BatcOjqbEaJRp5UDJbZNEo6TRViwX9XrNeb7hukEyr'
         b'/J7+t+4SKHDHiSZZ4/YqipwmIBAnGbBG+wF1SzjgWwWgyFEHkAaEALdMJEQo8Fnat5t'
         b'er1+c4sr1LluzURtbPEtLdmZqyU6XAjz0/yl8hu7Np9FoMn+4sPw3iY5UJ6OnlGI0W2'
         b'mvP+ZRZHnlVwEYAMpf3pXo7rooJTozRz6cqX5/SI6En+WOe849bCaQA2y7+b5EBxQd2'
         b'bm5MjVrjH3Y63xtteq5duVsLBbb8QUD7gOKgUzABRQZzDb7xtzJ0yYNe0SCfqp3b/aH'
         b'g/7vf0FxgAtAOrCSG+VP18mRSIGr4JM7z7E9rwVUJbYO6PgSABmI3RQXAEGnF6VzrSc'
         b'OqwDt9TVaZ9MJdzQcXPMlxG+FhAAfoApAhmSNeycmy/miKJ0PBYYWA51fAbAKaAIUoO'
         b'R/sS3nSt75BV4AAAAASUVORK5CYII=')
ICO_MI = (b'iVBORw0KGgoAAAANSUhEUgAAABgAAAAfCAYAAAD9cg1AAAAABHNCSVQICAgIfAhkiA'
          B'AAAAlwSFlzAAAOdQAADnUBuWNRMgAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBl'
          b'Lm9yZ5vuPBoAAAcXSURBVEiJpZZpdFTlGcd/d+7MvbNkJpNlCINkskDYIQQQCEuFlq'
          b'WUI1oVA22l0h7aGo/Vlg/2tOWc9pRaj5yqcCq0FFGpuLAYhVoMiKwSELJBSpiQEAgk'
          b'SIYks2/3zr39QBPZBHr6fLn3nPd5/v9nfd9H4O6Sb5SkpZJsma8oyQJBF4yapoqi0R'
          b'gURVNVNBx4H6gAlNsZC3cA9shm2waTLE0aef8MS97Q0aYMlxujSQIgGg7yZVsL3tqq'
          b'UHtrY0JTld8pirIW0O9KIIpimVE2/23qvDL78JIpBgSBUM9VfB1tREJ+DKKIM7s//e'
          b'7LxyTJhAM97PvwrUjnpdb6eDT8MODrw7oZ3GQylVvtztWPl69IH5A/RDjvPcnBnZtp'
          b'bazB6cogt2gwRpNAe+sZ9lVsIhzswe0ZzKhJMyRRNPbvvNRapqrKJiAOYLwJf6pksf'
          b'1xYfkKh0kys6/iDXRd5Vfr3mLwmJJbIo2GguzavJFta/9M6ZzHKJ462yQIwsAvPvto'
          b'byIWnQBo10dgkc2Wz+cveS47PcNF5fvrGDFxMr/d8B5Z/d23LZJJlhkxYTJTv/MQ/1'
          b'i1Aps9g6ElpeLltub0SMAf0LTUF4avUiMvKxhekpYzsIC6I7vJLRrCUytfRhDu1AfX'
          b'xJ1XyIvbKjlSuYVoKMCMBUusgsHwB0Dui8AoSdtnPb4sG+DQzs38acsuTLIMgK5pHP'
          b'90F9UH9tBUdwJv7XG8tcdxZrtIS3cCYHdmkNRF6g5WMmjkeK52nE91d3U29Ubgkc1W'
          b'mzMrB29dFbMWfh+r3QFAS0M9W/6yCpsjHZfiZ7rQwSTBh9Nup6mumu1/fQVVSQIw63'
          b'tLOe89iZJMMGzcNJvVkra0l6D0voKhOkDnpXNMnD0fgIZjn9N2tpFHn/olqRMfc7Hz'
          b'KqvCbjZclcm7XINBTTJ30ZO8t/pFVEXBarWRN3o8vo4LZLtz0bTUqF6CLLsz0wIQ6P'
          b'aRWzSUeDRC88kaZn53Ed7a4+jhINVBDfV0NU0znmDTRYWCQBNpzgwe/FE5le9sRElp'
          b'uPKLCHR1YnNkoCrJjF4C2WA0GQA0LYXRZKLHd4X0rGwAYuEQUUWlo+x5jMPG4a5YQ1'
          b'KUkXUNgDSHk5C/h5iqw3VNIQgCvQTt/q4rMQBnVj86Wltw5xWiJBJc8J5m2PhJ5Luc'
          b'jNq5mpRsQejvYaYzRUPqWp0+/PsaZpUtIZhI4b98EZvdiZJMAIZ4L8FpX8cFFSArJ5'
          b'ea/XsAmLP4SZrqTlB7cC9dY+ax2A1l/hp+QjOy3cmwuY/y7qsvUPrtBegOF2pKpaX6'
          b'CDmeQr682IJkMTf0EYS6u4gE/RQVT+Zfb7/e1xmzy5ZQMGI03voaao0DqdcyOKb3wy'
          b'dlcarqEI/87BekDyzkalTl5J4duD2DkM1WWhvr4rFQYFtfwkyy5ZWxU+f8dOK3FliO'
          b'VG5lUMl4lv3697cMla7rNwxfKJGiPZQkHPDzatk3+OZDP8SRmc2ml54PJeIRT9+gaS'
          b'm12tfR9vSQ4slmz+CR7N26kbjRSsHIYiTxxsIBxBSNKxEFX1QlFg7xxjOLKBxSTP6w'
          b'Yo59WhH3Xb6wMaUqFdffRVHBIHS1n2ucNvL+BywFQ8ey++3XONNwCnvROBRRIpTU6I'
          b'mrdEZUumMqiZRO8/FDvPnsYjyFIxg9eSYXzzboR3d/0JmIRx8GlFsuGpNsXp8zsGDR'
          b'/Cd+bjcYROqP7qWp/igFJZPIHzcFa3omAJ2tXhr27kTQdCbOXEBObiGXWhr1Xe+u9S'
          b'dj0SnAGbj9gyOIJnlNmt3x47mLyy2uAR40TaOt6RT+7k5ikRAmScJitePOKyKz3wA0'
          b'TaP6wMfJ+sOVXYl4bDbw7z6w2xC4bI7MOnNO4YDolXO4+g9IFpfOltz5RZgk+QbFYL'
          b'cPyWJJtjef+WT/jk098WjkWSBwg7c3gTtsDmfThJkP5uSNnsLJhlN4977j17VUlZpM'
          b'TJctVsUkyQZd01PRcMAiisYrRtm8POzv+uA2jgI3vWiyLW27qio5AgJpshFbsgvQNs'
          B'YjoeUAqpJ0AjlADPApJGLEIl+HfaOIoviIy1MYWLJyvT5k/DQ9252rZ7s9KvDAvSF8'
          b'De5/v5Jktnw2v/w3mc5+bgaNK0Wy2GiuOexXFeXp/4fACFD+2pZMX9t5OdOd23dw6u'
          b'AnQSURf4ab9pyb5AjwMvBPoBFYyLWIy4AwsE4ESqLB4PaR0+d4eq3OHj+oeY/tr1OS'
          b'iefu4uBjgAmwAIXAAWAr4AI+AioMFrtjfeHYiWN6LRLRMAe3vh6OR8M/uIcM6EAImA'
          b'dU3U7BoCQSIzwjvtp5Dm97M6KpqdVAyz0QAGwDGviaVBpEk3zGe3S/BtBcU6W31h/1'
          b'JePRlfcIDtdyv/pOCgNlW1q1UZLDFpujFij4H8BfuO5/CTAcWA7s4NrGvfA/XProFL'
          b'yZN48AAAAASUVORK5CYII=')
ICO_MO = (b'iVBORw0KGgoAAAANSUhEUgAAABgAAAAfCAYAAAD9cg1AAAAABHNCSVQICAgIfAhkiA'
          b'AAAAlwSFlzAAAOdQAADnUBuWNRMgAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBl'
          b'Lm9yZ5vuPBoAAAcrSURBVEiJpZZpdFTlGcd/d+7MvTOZzGSyDGGQTBYISwKEALJToW'
          b'WpUtGqGGgrlXpoazxWWz/YY+Uce0qtR05VOBVbiogUXFiMlVoMGIGwC9kgJUxICAQI'
          b'kiHJ7Nu9c28/QMIiCj19vrz3nnuf///5P8v7vgK3tzyjJC2WZMtcRUnkC7pg1DRVFI'
          b'3GgCiaDkZC/g+BCkC5lbPwLcBu2WxdY5KlCcV3T7fkDh1pSne6MJokACKhAF+1t+Kp'
          b'Oxi80NYU11TlJUVRVgH6bQlEUSwzyua/Tbm3zDa8dLIBQSDYcxlvRzvhoA+DKOLI6k'
          b'+/u/IwSTIhfw+7Pn433Hm+rSEWCT0IePuwbgY3mUzlKTbHikfLl6YNyBsinPEco3rb'
          b'RtqaanE408kpHIzRJHCh7SS7KtYTCvTgcg9mxITpkiga+3eebytTVWU9EAMw3oQ/Rb'
          b'JY/zi/fKndJJnZVfEOuq7y27feZfCo0q8pjQQDbN+4li2r/syk2Y9QMmWWSRCEgV9+'
          b'8c+qeDQyDtCuV2CRzZb9cxc9m5WW7qTyw7coGj+RF9d8QGZ/1y2LZJJlisZNZMp9D/'
          b'CP5Uux2tIZWjpJvNjekhb2+/yalvzScC018pL84aWp2QPzqT+wg5zCITy57DUE4dv6'
          b'4Iq5cgt4ZUslByo3EQn6mT5vUYpgMPwBkPsUGCVp68xHl2QB7N22kT9t2o5JlgHQNY'
          b'0jn2+nZs9OmuuP4qk7gqfuCI4sJ6lpDgBsjnQSukh9dSWDisdyueNMsrurs7lXgVs2'
          b'p1gdmdl46g8yc/6PSbHZAWhtbGDTX5ZjtafhVHxMEzqYIHhx2Gw019ew9a+voyoJAG'
          b'b+aDFnPMdQEnGGjZlqTbGkLu4lmHRX/lAdoPP8acbPmgtA4+H9tJ9q4uEnf0Py6Kec'
          b'67zM8pCLNZdlci/WYlATzFnwOB+seAVVUUhJsZI7cizejrNkuXLQtOSIXoJMmyPDAu'
          b'Dv9pJTOJRYJEzLsVpm/HABnroj6KEANQEN9UQNzdMfY/05hXx/M6mOdO7/WTmV761F'
          b'SWo48wrxd3VitaejKon0XgLZYDQZADQtidFkosd7ibTMLACioSARRaWj7HmMw8bgql'
          b'hJQpSRdQ2AVLuDoK+HqKrDdU0hCAK9BBd8XZeiAI7MfnS0teLKLUCJxznrOcGwsRPI'
          b'czoYsW0FSdmC0N/NDEeSxuSVOn3895XMLFtEIJ7Ed/EcVpsDJREHDLFeghPejrMqQG'
          b'Z2DrW7dwIwe+HjNNcfpa66iq5R97LQBWW+Wn5OC7LNwbA5D/P+Gy8z6fvz0O1O1KRK'
          b'a80Bst0FfHWuFclibuwjCHZ3EQ74KCyZyL83vN3XGbPKFpFfNBJPQy11xoE0aOkc1v'
          b'vhlTI5fnAvD/3y16QNLOByROXYzk9wuQchm1Noa6qPRYP+LX0JM8mW10dPmf2L8d+b'
          b'ZzlQuZlBpWNZ8sLvvzZUuq7fMHzBeJILwQQhv483yr7Ddx/4KfaMLNa/+nwwHgu7+w'
          b'ZNS6o13o72p4aUTDS7BxdTtXktMWMK+cUlSOKNhQOIKhqXwgreiEo0FOSdpxdQMKSE'
          b'vGElHP68Iua9eHZtUlUqrt+LIoJB6Lpwumlq8d33WPKHjmbHhjc52XgcW+EYFFEimN'
          b'Doial0hlW6oyrxpE7Lkb2se2Yh7oIiRk6cwblTjfqhHR91xmORBwHlaxuNSTavzh6Y'
          b'v2DuY7+yGQwiDYeqaG44RH7pBPLGTCYlLQOAzjYPjVXbEDSd8TPmkZ1TwPnWJn37+6'
          b't8iWhkMnASbn3gCKJJXplqsz8xZ2G5xTnAjaZptDcfx9fdSTQcxCRJWFJsuHILyeg3'
          b'AE3TqNnzaaJhX2VXPBadBfynD+wWBE6rPaPenF0wIHLpNM7+AxIlk2ZJrrxCTJJ8w4'
          b'+Bbi+SxZK40HLys92frO+JRcLPAP4bor0J3G61O5rHzbg/O3fkZI41HsdT9Z5P15IH'
          b'1UR8mmxJUUySbNA1PRkJ+S2iaLxklM3PhXxdH90iUOCmE022pm5VVSVbQCBVNmJNdA'
          b'Ha2lg4+ByAqiQcQDYQBbwK8SjR8Ddh32iiKD7kdBf4Fy1brQ8ZO1XPcuXoWS63Ctxz'
          b'ZwjfgHt1lSSz5Yu55b/LcPRzMWjMJCSLlZbafT5VUZ76fwiMAOVvbsrwtp+RM1w5fR'
          b'+OV38WUOKxp7npnnOTHQBeA/4FNAHzgQHAE4AJeEEESiOBwNbiabPdvV6njlRrnsO7'
          b'65VE/NnbBPgIIAFmYBCwB3gJ+AGwH3jRYLHZVxeMHj+q1yMeCVG9+e1QLBL6yR1kQA'
          b'cCwH1X1XCVLAG0AYMNSjxe5C66dufZt2VdWFOTK4DWOyAA2AI0ci2V2tXVAKgG0SSf'
          b'9BzarQG01B7U2xoOeROxyLI7BIcruV9x3XsAyALGAfUAA2Vrao1RkkMWq70OyP8fwF'
          b'++7nkRMBwoATYA6wDXfwHHr+xKYDz/CQAAAABJRU5ErkJggg==')
ICO_MOI = (b'iVBORw0KGgoAAAANSUhEUgAAABgAAAAfCAYAAAD9cg1AAAAABHNCSVQICAgIfAhki'
           b'AAAAAlwSFlzAAAOdQAADnUBuWNRMgAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYX'
           b'BlLm9yZ5vuPBoAAAdKSURBVEiJpZZ5dFTVHcc/b97MezOZzGSyEQbIZIEAsoUAslu'
           b'hZalyRIuFgAuV9lBqPNa2/GE3etpTWz3lVIVToVCISgWU1cqxGBCBgCyGbJASJiQE'
           b'AgmQIclMZp/35r3+QRICBO05/f1z733v3s/3/n6/uwl8s2UbJWmZJFvmKUosR9AFo'
           b'6apomg0doqi6WQo4PsI2AsofQ0Wvgbsks3WTSZZmjTy4RmWrGGjTcnpTowmCYBQoJ'
           b'MbTQ24K0/6mxtro5qq/F5RlHWA/o0CoigWGmXzhmmPFdoeKphqQBDwd9zC09JE0O/'
           b'FIIo40vrTb2A2Jkkm4Ovg8MfvB1uvNVZHQoGnAE8P6164yWQqSrA51iwqWpU0IHuo'
           b'cNl9ltJ9W2msrcCRnkxm3hCMJoHmxgsc3ruFQGcHTtcQRk2aIYmisX/rtcZCVVW2A'
           b'BEA4z38aZLF+qeFRavsJsnM4b3vousqv1z/PkPGFNznacjfyf6txexa91emzPk++d'
           b'NmmwRBGPTVF/86FA2HJgBabw8sstny5bylP0tLSk6n5KP1jJg4md9u+pDU/s4+k2S'
           b'SZUZMmMy0x5/kn6tXYbUlM6xgini9qT4p6PP6NC3+leFOaOTlOQ8VJGYMyqHqxAEy'
           b'84by4mtvIghftw5umzMrlzd2lXCiZAchv48Z85cmCAbDHwG5xwOjJO2etWh5GsCxf'
           b'Vt5fcd+TLIMgK5plH2+n/KjB6mrOoO7sgx3ZRmOtHQSkxwA2BzJxHSRqtISBo8cz6'
           b'2Wy/H2tta6bg9csjnB6kjNwF11klkLnyXBZgegoaaaHX9bjdWeRLri5RGhhUmCB4f'
           b'NRl1VObv//haqEgNg1jPLuOw+ixKLMnzcdGuCJXFZt8CUgTnDdIDWa5eYOHseADWn'
           b'v6TpYi1Pv/gL4mc+5WrrLVYHnGy6JZN1vQKDGmPu4hf4cM0bqIpCQoKVrNHj8bRcI'
           b'c2ZiabFR3ULpNocKRYAX7uHzLxhREJB6s9WMPN7i3FXlqEHOinv1FDPl1M343m2XF'
           b'XI8dWR6EjmiR8WUbKtGCWukZ6dh6+tFas9GVWJJXcLyAajyQCgaXGMJhMdnpskpaY'
           b'BEA74CSkqLYWvYhw+DufetcREGVnXAEi0O/B7OwirOvRaFIIg0C3Q7G27GQZwpPaj'
           b'pbEBZ1YuSjTKFfd5ho+fRHa6g1H71hCXLQj9Xcx0xKmJ387Tx/9Yy6zCpXRG43ivX'
           b'8Vqc6DEooAh0i1w3tNyRQVIzcik4shBAOYseYG6qjNUlh6ibcxjLHFCobeCH1OPbH'
           b'MwfO7TbH/7z0z57nx0ezpqXKWh/AQZrlxuXG1AsphregT87W0EO73k5U/m3x9s7lk'
           b'ZswuXkjNiNO7qCiqNg6jWkjmt98MjpXLu5DEW/OTnJA3K5VZI5ezBT3C6BiObE2is'
           b'rYqE/b5dPQEzyZa3xk6bs2Lid+ZbTpTsZHDBeJb/+g/3bSpd1+/afP5onGZ/jIDPy'
           b'9uF3+LbT/4Ae0oaW/7yqj8aCbp6NpoWV8s9LU0vDc2fbHYNGcmhncVEjAnkjMxHEu'
           b'9OHEBY0bgZVPCEVMIBP+++vJjcoflkD8/n9Od7I57rV4rjqrK391kUEgxCW/Ol2uk'
           b'jH37UkjNsLAc+eIcLNeew5Y1DESX8MY2OiEprUKU9rBKN69SXHeO9V5bgyh3B6Mkz'
           b'uXqxRj91YE9rNBJ6ClDuO2hMsnljxqCcxfOe/6nNYBCpPnWIuupT5BRMInvcVBKSU'
           b'gBobXRTc2gfgqYzceZ8MjJzudZQq+/fvs4bC4emAheg7wtHEE3y2kSb/UdzlxRZ0g'
           b'e40DSNprpzeNtbCQf9mCQJS4INZ1YeKf0GoGka5Uc/jVUfL2mLRsKzgf/0wPoQSLf'
           b'aU6rMGbkDQjcvkd5/QCx/ymzJmZ2HSZLv6tjZ7kGyWGLN9Rc+O/LJlo5IKPgK4Ltr'
           b'tvfA7Va7o27CzCcyskZP5WzNOdyHtnl1LX5SjUUfkS0JikmSDbqmx0MBn0UUjTeNs'
           b'nllwNu2p4+JAvfcaLI1cbeqKhkCAomyEWusDdCKI0H/SgBViTmADCAMeBSiYcLBB7'
           b'HvNlEUF6S7cn1LX9uoDx0/XU9zZuppTpcKPPq/ER7A7SolyWz5Yl7Rb1Ic/ZwMHjc'
           b'FyWKlvuK4V1WUl/4fASNA0Ts7UjxNl+UUZ2bPj3Oln3Uq0cjL3HnnJAJ7gGcAO7Ae'
           b'mAs8CzwOeIGVQCrwO2Ag0GwACo5u31zSL2uIvRt+saxU8964dj4ej2/rNRkTkAwsA'
           b'BZ2gazACuA5wA0sApq7vqUCKwwWm31j7tiJY7op0VCA0p2bA5FQ4Lk+PHYDQ7md6F'
           b'YgF7jY5WUlMObeAQYlGh3hGnHnzXN813tBTY2vARr6iilwCSjvqou9Qqhx/zsLg2i'
           b'SL7hPHdEA6itO6o3VpzyxSOi1B8AB1gFbu+qXgayuel6Xh/fZINmaWG6U5IDFaq8E'
           b'ch4ATgLe7NUu7ip/BWwDdnX1GQhsACqADf8FzRDv5zdXrpYAAAAASUVORK5CYII=')
ICO_PI = (b'iVBORw0KGgoAAAANSUhEUgAAABgAAAAfCAYAAAD9cg1AAAAABHNCSVQICAgIfAhkiA'
          b'AAAAlwSFlzAAAOdQAADnUBuWNRMgAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBl'
          b'Lm9yZ5vuPBoAAAcaSURBVEiJpZZpdFRnGcd/d5Z7ZzKZyWRnaDJZIEDDEkLYAtSCso'
          b'hYWltpQC2CHtSmp1blQz1VznFB7ZFTKZwWFIG2WJayNAin0kBTIFACDdkgEhISAiEJ'
          b'kCHJTGafe+deP2BSCFDw+Hx5P7zP8/8/6/s+Ag+XTIMoLhcl8wJZjmQJmmBQVUWvNx'
          b'j69HpjRcDn+QAoAeT7GQtfAuyUTJbNRkmcMnrSTHPGyLHG+GQHBqMIQMDXx422Fhpr'
          b'KrwdrQ1hVZF/I8vyBkB7KIFery8ySKa/TZ9fZH08f5oOQcDbewtXZxt+rxudXo89aQ'
          b'gpj2ViFCV8nl6O7n/P39XeWhcK+J4BXANYg8GNRmNxjNW+7vniVXFDM0cIVxrPUX5w'
          b'O60N1diT40nPGY7BKNDRepGjJdvw9fXicA5nzJSZol5vGNLV3lqkKPI2IARgGIQ/XT'
          b'Rb/rCoeJXNKJo4WvIOmqbwy43vMXxc/j2RBrx9HNq+lb0b3qBw7rfJmz7HKAhC2uef'
          b'/rMsHAxMBNQ7IzBLJvNnC5b+LCkuPpnSDzaSO3kqv968i8QhjvsWyShJ5E6cyvRvPM'
          b'0/1qzCYo1nZH6h/npbc5zf4/aoavRz3RepkVZkPZ4fm5qWRe2pw6TnjODF1X9BEL6s'
          b'D26LIyOb1/eWcqp0NwGvh5kLl8YIOt3vAWkgAoMo7pv9/IokgBMHt/On3YcwShIAmq'
          b'pS+ckhqo4foan2LI01lTTWVGJPSiY2zg6A1R5PRNNTW17KsNEF3Oq8Eu3p7mrqj8Ap'
          b'mWIs9sRUGmsrmL3ou8RYbQC01Nex+601WGxxJMtunhA6mSK4sFutNNVWse+va1HkCA'
          b'Czv7OcK43nkCNhRk2YYYkxxy7vJyh8LGukBtDVfpnJcxYAUH/mM9ouNfDci78gevYj'
          b'rnXdYo3PweZbEhnXq9EpEeYtXsauda+jyDIxMRYyxhbg6rxKkiMdVY2O6SdItNoTzA'
          b'CeHhfpOSMJBfw0n6tm1rcW01hTiebro6pPRblQRdPMF9h2TSbL00SsPZ6nflBM6Y6t'
          b'yFGV5MwcPN1dWGzxKHIkvp9A0hmMOgBVjWIwGul13SQuMQmAoM9LQFboLHoVw6gJOE'
          b'rWE9FLSJoKQKzNjtfdS1DR4I6mEASBfoIOd/fNIIA9MYXO1hYcGdnI4TBXGy8wqmAK'
          b'mcl2xhxcR1QyIwxxMssepT56u077/76e2UVL6QtHcV+/hsVqR46EAV2on+CCq/OqAp'
          b'CYmk71sSMAzF2yjKbas9SUl9E9bj5LHFDkruZHNCNZ7Yya9xw73/wjhV9fiGZLRokq'
          b'tFSdItWZzY1rLYhmU/0AgbenG3+fm5y8qfzr/S0DnTGnaClZuWNprKumxpBGnRrPGS'
          b'0Fl5jI+YoTPPuTnxOXls2tgMK5IwdwOIchmWJobagNBb2evQMJM0rmteOnz/3x5K8t'
          b'NJ8q3cOw/AJWvPbbe4ZK07S7hs8bjtLhjeDzuHmz6Ct89envY0tIYtufX/WGQ37nwK'
          b'CpUaXK1dn20oi8qSbn8NGU7dlKyBBD1ug8RP3dhQMIyio3/TKugELQ5+WdlxeTPSKP'
          b'zFF5nPmkJOS6fnVrVJFL7nyLAoJO6O643DBj9KQnzVkjx3P4/be5WH8ea84EZL2IN6'
          b'LSG1Lo8iv0BBXCUY3myhO8+8oSnNm5jJ06i2uX6rXThz/sCocCzwDyPQ+NUTJtSk3L'
          b'WrzghZ9adTo9dafLaKo7TVb+FDInTCMmLgGArtZG6ssOIqgak2ctJDU9m/aWBu3Qzg'
          b'3uSDAwDbgI9/9wBL1RWh9rtf1w3pJic/JQJ6qq0tZ0HndPF0G/F6MoYo6x4sjIISFl'
          b'KKqqUnX8o0jdydLucCg4B/j3ANh9CJIttoRaU2r20MDNyyQPGRrJK5wjOjJzMIrSXY'
          b'p9PS5EsznS0Xzx42MHtvWGAv5XAM9d3g4Ct1ls9qaJs55KzRg7jXP152ks2+HW1GiF'
          b'Egk/IZljZKMo6TRViwZ8HrNeb7hpkEwrfe7uD+/jKDDoR5MssfsURU4VEIiVDFgi3Y'
          b'C6NeT3rgRQ5IgdSAWCgEsmHCTofxD23aLX659NdmZ7lq7epI0omKElOdK1JIdTAZ58'
          b'NIQH4P73FEWT+dMFxb9KsKc4GDahENFsobn6pFuR5Zf+HwIDQPHbuxNcbVekBEf6wM'
          b'X58o/75HDoZQbtOYPkNWASEAYuAL8DVgJFgA/YqAPyj+/cUpqSMdzWb3Wpslx132i/'
          b'EI1GdzzEQRPwFrAYmA/YgDeA/cBaYI/BbLVtyh4/eVy/RTjgo3zPFl8o4PveI+UAcr'
          b'jdjWbgnoob5HA415n7xc5zcu+7flWJrgNaHpGgAFCBbwLRwZc6vVG62Hj6mArQXF2h'
          b'tdaddkVCgdWPCA6wC9gEtD9IIU2yxFYZRMlntthqgKz/AXwZMHjlWwkc4PbGveg/ud'
          b'HmRALt5c0AAAAASUVORK5CYII=')
ICO_PO = (b'iVBORw0KGgoAAAANSUhEUgAAABgAAAAfCAYAAAD9cg1AAAAABHNCSVQICAgIfAhkiA'
          b'AAAAlwSFlzAAAOdQAADnUBuWNRMgAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBl'
          b'Lm9yZ5vuPBoAAAcrSURBVEiJpZZrUFTnGcd/Zy/n7LLsstxdA8tFUIMXxDtqGm291N'
          b'qYNKlB28ZqM7YNGZu2mUw6ts70YtNMnTbRSUxr1RjrLV5CGic1aIiKRjTITakIgigC'
          b'Kiuwy973nD2nHxSixEQ7fb685533PP//c33fR+D+kmkQxeWiZF4gy5EsQRMMqqro9Q'
          b'ZDn15vrAj4PO8CJYB8L2XhK4CdksmyySiJU0ZNmmnOGDHGGJ/swGAUAQj4+rje1kJj'
          b'TYW3o7UhrCryb2VZ3gBo9yXQ6/VFBsn09+nzi6wPF0zTIQh4e2/i6mzD73Wj0+uxJw'
          b'0h5aFMjKKEz9PLkfff8Xe1t9aFAr4nANcA1mBwo9FYHGO1r3u6eHXc0MzhwuXGs5Qf'
          b'2EFrQzX25HjSc3MwGAU6Wi9wpGQbvr5eHM4cRk+ZKer1hiFd7a1FiiJvA0IAhkH400'
          b'Wz5Y+LilfbjKKJIyVvo2kKv3rrHXLGFnzB04C3j4M7trBvw18onPtd8qfPMQqCkPbZ'
          b'J/8qCwcDEwH1Tg/Mksn86YKlP0+Ki0+m9N23yJs8ld9s2k3iEMc9k2SUJPImTmX6tx'
          b'7nn2tXY7HGM6KgUH+trTnO73F7VDX6me7z0Egrsh4uiE1Ny6L25CHSc4fz3Jq/Ighf'
          b'VQe3xJGRzav7SjlZuoeA18PMhUtjBJ3uD4A04IFBFPfPfnpFEsDxAzv4056DGCUJAE'
          b'1Vqfz4IFXHDtNUe4bGmkoaayqxJyUTG2cHwGqPJ6LpqS0vZdioCdzsvBzt6e5q6vfA'
          b'KZliLPbEVBprK5i96PvEWG0AtNTXseeNtVhscSTLbh4ROpkiuLBbrTTVVrH/b6+hyB'
          b'EAZn9vOZcbzyJHwowcP8MSY45d3k9Q+FDWCA2gq/0Sk+csAKD+9Ke0XWzgqed+SfTM'
          b'h1ztuslan4NNNyUyrlWjUyLMW7yM3eteRZFlYmIsZIyZgKvzCkmOdFQ1OrqfINFqTz'
          b'ADeHpcpOeOIBTw03y2mlnfWUxjTSWar4+qPhXlfBVNM59h21WZLE8TsfZ4HvtRMaU7'
          b'tyBHVZIzc/F0d2GxxaPIkfh+AklnMOoAVDWKwWik13WDuMQkAII+LwFZobPoZQwjx+'
          b'MoWU9ELyFpKgCxNjtedy9BRYM7ikIQBPoJOtzdN4IA9sQUOltbcGRkI4fDXGk8z8gJ'
          b'U8hMtjP6wDqikhlhiJNZ9ij10Vt5ev8f65ldtJS+cBT3tatYrHbkSBjQhfoJzrs6ry'
          b'gAianpVB89DMDcJctoqj1DTXkZ3WPns8QBRe5qfkwzktXOyHlPsev1Vyj85kI0WzJK'
          b'VKGl6iSpzmyuX21BNJvqBwi8Pd34+9zk5k/l39s3D1TGnKKlZOWNobGumhpDGnVqPK'
          b'e1FFxiIucqjvPkT39BXFo2NwMKZw9/gMM5DMkUQ2tDbSjo9ewbCJhRMr82bvrcn0z+'
          b'xkLzydK9DCuYwIpVv/tCU2madlfzecNROrwRfB43rxd9ja8//kNsCUls+/PL3nDI7x'
          b'xoNDWqVLk6254fnj/V5MwZRdneLYQMMWSNykfU3504gKCscsMv4wooBH1e3l65mOzh'
          b'+WSOzOf0xyUh17UrW6KKXHLnXRQQdEJ3x6WGGaMmPWrOGjGOQ9vf5EL9Oay545H1It'
          b'6ISm9Iocuv0BNUCEc1miuPs/WFJTiz8xgzdRZXL9Zrpw691xUOBZ4A5C9cNEbJtDE1'
          b'LWvxgmd+ZtXp9NSdKqOp7hRZBVPIHD+NmLgEALpaG6kvO4CgakyetZDU9GzaWxq0g7'
          b's2uCPBwDTgAtz7wRH0Rml9rNX27LwlxebkoU5UVaWt6Rzuni6Cfi9GUcQcY8WRkUtC'
          b'ylBUVaXq2IeRuhOl3eFQcA7wnwGwexAkW2wJtabU7KGBG5dIHjI0kl84R3Rk5mIUpb'
          b't+7OtxIZrNkY7mCx8d/WBbbyjgfwHw3GXtIHCbxWZvmjjrsdSMMdM4W3+OxrKdbk2N'
          b'ViiR8COSOUY2ipJOU7VowOcx6/WGGwbJ9KLP3f3ePQwFBr1okiV2v6LIqQICsZIBS6'
          b'QbULeE/N4XARQ5YgdSgSDgkgkHCfq/DPtu0ev1TyY7sz1L12zUhk+YoSU50rUkh1MB'
          b'Hn0whC/Bvb2Kosn8yYLiXyfYUxwMG1+IaLbQXH3Crcjy8/8PgQGg+M09Ca62y1KCI3'
          b'3g4Fz5R31yOLSSQXPOIFkFTALCwHng98BC4FnACKzSAQXHdm0uTcnIsfVrXawsV93X'
          b'289Ho9Gd9zHQBLwBLAbmAzbgJWARsBJ4yWC22jZmj5s8tl8jHPBRvnezLxTw/eCBYg'
          b'C53KpGM+C/TRoBWoEcgxwO5znzPp95Tuzb6leV6Dqg5QEJJgAq8G0gevsbQAcoOr1R'
          b'utB46qgK0FxdobXWnXJFQoE1DwgOsBvYCLTf3vcBScBEoBYgTbLEVhlEyWe22GqArP'
          b'8BfBkweOTLB7YDWwHHfwEICenCRsuwaAAAAABJRU5ErkJggg==')
ICO_POI = (b'iVBORw0KGgoAAAANSUhEUgAAABgAAAAfCAYAAAD9cg1AAAAABHNCSVQICAgIfAhki'
           b'AAAAAlwSFlzAAAOfgAADn4BMFB4OgAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYX'
           b'BlLm9yZ5vuPBoAAAdDSURBVEiJpZZ9cBT1Gcc/ey+7d7nc5fLOAbm8QADDSwggEMA'
           b'KLS9VRrRaCVSlYodSYy1tmSl9o9NObevItApVLBRQUUB5MVbGYsAIBORFyBukwIWE'
           b'QCABcnm5y73f7u32D5JIQsDO9JnZ2Zlndz/f5+X3++0j8PWWZRDFpaJkni/L0WxBE'
           b'wyqquj1BkOXXm88HvR7PwBKAHmgj4V7gJ2SybLJKIlTRt8/05w5cqwxMdWBwSgCEP'
           b'R3caOpAVfVcV9z4/mIqsi/l2V5PaB9rYBery8ySKYN0x8qst5XME2HIODrbMPd0kT'
           b'A50Gn12NPGUTakCyMooTf28nBj94JtF5rrAkH/Y8B7l5Wf7jRaCyOs9rXLixenTA4'
           b'a4Rw2XWG8r3baDxfiT01kYzc4RiMAs2NFzhYshV/VycO53DGTJkp6vWGQa3XGosUR'
           b'd4KhAEM/fjTRbPlT08Wr7YZRRMHS95C0xR++eY7DB9XcEemQV8X+7ZtYff6v1I497'
           b'vkT59jFARh6Jef/6ssEgpOAtTbMzBLJvMX85f8NCUhMZXSD94kb/JUfrvpfZIHOQZ'
           b'sklGSyJs0lekPP8q7a1ZjsSYysqBQf72pPiHg9XhVNfal7qvSSMuy7yuITx+aTfWx'
           b'/WTkjuD5l/6GINxrHdwyR2YOL+8u5VjpToI+LzMXLIkTdLo/AlJvBgZR3DN74bIUg'
           b'CN7t/GXnfswShIAmqpy6rN9VBw+QF31aVxVp3BVncKekkp8gh0Aqz2RqKanuryUYa'
           b'Mn0tZyOdbR3lrXk4FTMsVZ7MnpuKqPM/vJp4iz2gBoqK1h5+trsNgSSJU9PCC0MEV'
           b'wY7daqauuYM8/XkWRowDM/t5SLrvOIEcjjJowwxJnjl/aI1A4JHukBtB67RKT58wH'
           b'oPbkFzRdPM8Tz/+c2OlPuNraxhq/g01tEpnXK9EpUeYtepb3176MIsvExVnIHDsRd'
           b'8sVUhwZqGpsTI9AstWeZAbwdrjJyB1JOBig/kwls76zCFfVKTR/FxVdKsq5CupmPs'
           b'PWqzLZ3jri7Yk88lwxpdu3IMdUUrNy8ba3YrElosjRxB4BSWcw6gBUNYbBaKTTfZO'
           b'E5BQAQn4fQVmhpWgVhlETcJSsI6qXkDQVgHibHZ+nk5CiwW2LQhAEegSaPe03QwD2'
           b'5DRaGhtwZOYgRyJccZ1j1MQpZKXaGbN3LTHJjDDIySx7jNrYrT599M91zC5aQlckh'
           b'uf6VSxWO3I0AujCPQLn3C1XFIDk9AwqDx0AYO7iZ6mrPk1VeRnt4x5isQOKPJX8kH'
           b'okq51R855gx2t/pvDbC9BsqSgxhYaKY6Q7c7hxtQHRbKrtFfB1tBPo8pCbP5V/v7e'
           b'5d2XMKVpCdt5YXDWVVBmGUqMmclJLwy0mc/b4ER7/0c9IGJpDW1DhzIGPcTiHIZni'
           b'aDxfHQ75vLt7C2aUzK+Onz53+eRvLTAfK93FsIKJLPv1H+7YVJqm9dl8vkiMZl8Uv'
           b'9fDa0Xf4JuPfh9bUgpbX1nli4QDzt6NpsaUCndL0wsj8qeanMNHU7ZrC2FDHNmj8x'
           b'H1fRsHEJJVbgZk3EGFkN/HWy8uImdEPlmj8jn5WUnYff3Klpgil9x+FgUFndDefOn'
           b'8jNH3P2jOHjme/e+9wYXas1hzJyDrRXxRlc6wQmtAoSOkEIlp1J86wtsrFuPMyWPs'
           b'1FlcvVirndj/YWskHHwMkO84aIySaWP60OxF85/5iVWn01Nzooy6mhNkF0wha8I04'
           b'hKSAGhtdFFbthdB1Zg8awHpGTlcaziv7dux3hMNBacBF2DgH46gN0rr4q22H8xbXG'
           b'xOHexEVVWa6s7i6WglFPBhFEXMcVYcmbkkpQ1GVVUqDn8SrTla2h4Jh+YA/+mFDSC'
           b'QarElVZvScwYHb14iddDgaH7hHNGRlYtRlPq82NXhRjSbo831Fz499PHWznAwsALw'
           b'9om2H9xmsdnrJs16JD1z7DTO1J7FVbbdo6mx40o08oBkjpONoqTTVC0W9HvNer3hp'
           b'kEyrfR72j8cIFCg3x9NssTvURQ5XUAgXjJgibYD6pZwwLcSQJGjdiAdCAFumUiIUO'
           b'Bu7L6m1+sfT3XmeJe8tFEbMXGGluLI0FIcTgV48H8j3IXbfRdFk/nz+cW/SbKnORg'
           b'2oRDRbKG+8qhHkeUX/h8BA0DxGzuT3E2XpSRHRu+Ds+WfdsmR8Iv0nXNeAeyABPwd'
           b'OA08BTwMeICVQDLwO2AI0KwDCg7v2Fyaljnc1kO5eKpc9dy4di4Wi23vF9AEYAXwC'
           b'2AdYAGWA08DLmAh0NztSwaW68xW28ac8ZPH9RAiQT/luzb7w0H/0/fIfDC35p4coL'
           b'47yyog/44SyZFInjPvq5nn6O63A6oSWws03AX+OtAGPNddLrXbrzLAIKfTG6ULrhO'
           b'HVID6yuNaY80JdzQcfOke0f8YWAVc7r4yu/253CrTHTZUssRXGETJb7bYqoDse8Df'
           b'BUz9fL8CtgO7gQRuNXcDUAls+C9j2PAQ2V1dxQAAAABJRU5ErkJggg==')
LOADING = '../autoauditor/gui_files/loading.gif'

# Copyright

COPYRIGHT = """
AutoAuditor  Copyright (C) 2020 Sergio Chica Manjarrez @ pervasive.it.uc3m.es.
Universidad Carlos III de Madrid.
This program comes with ABSOLUTELY NO WARRANTY; for details check below.
This is free software, and you are welcome to redistribute it
under certain conditions; check below for details.
"""

# MAIN Window
MAIN_ABOUT_NAME = 'AutoAuditor'
MAIN_ABOUT_VER = 'v2.2'
MAIN_ABOUT_AUTHOR = 'Sergio Chica Manjarrez'
MAIN_ABOUT_LAB = 'Pervasive Computing Laboratory'
MAIN_ABOUT_DEPT = "Telematic Engineering Department"
MAIN_ABOUT_UC3M = 'Universidad Carlos III de Madrid, Leganés'
MAIN_ABOUT_LOC = 'Madrid, Spain'
MAIN_ABOUT_ACK = """This work has been supported by National R&D Projects TEC2017-84197-C4-1-R,
TEC2014- 54335-C4-2-R, and by the Comunidad de Madrid project CYNAMON
P2018/TCS-4566 and co-financed by European Structural Funds (ESF and FEDER)."""
MAIN_ABOUT_YEAR = date.today().strftime('%Y')

MAIN_LIC_C_H = 19
MAIN_LIC_C_H2 = 30
MAIN_LIC_C_SZ = (84, MAIN_LIC_C_H)

K_GIF = 'k_gif'
K_MINFO_COL = 'k_minfo_col_'
K_O_ML = 'k_o_ml_'
K_OINFO_ML = 'k_oinfo_ml_'

K_MAIN_ABOUT_P = 'kmain_about_p'
K_MAIN_TAB = 'kmain_tab'
K_MAIN_INFO_DEF = 'kmain_info_def'
K_MAIN_LFINFO = 'kmain_lfinfo'
K_MAIN_LF_FB = 'kmain_lf_fb'
K_MAIN_LDINFO = 'kmain_ldinfo'
K_MAIN_LD_FB = 'kmain_ld_fb'
K_MAIN_RCINFO = 'kmain_rcinfo'
K_MAIN_RC_FB = 'kmain_rc_fb'
K_MAIN_RC_CB = 'kmain_rc_cb'
K_MAIN_RC_CB_T = 'kmain_rc_cb_t'
K_MAIN_VPN_CB = 'kmain_vpn_cb'
K_MAIN_VPN_CB_T = 'kmain_vpn_cb_t'
K_MAIN_VPN_CFINFO = 'kmain_vpn_cfinfo'
K_MAIN_VPN_CF_T = 'kmain_vpn_cf_t'
K_MAIN_VPN_CF_FB = 'kmain_vpn_cf_fb'
K_MAIN_BC_CB = 'kmain_bc_cb'
K_MAIN_BC_CB_T = 'kmain_bc_cb_t'
K_MAIN_BC_CFINFO = 'kmain_bc_cfinfo'
K_MAIN_BC_CF_T = 'kmain_bc_cf_t'
K_MAIN_BC_CF_FB = 'kmain_bc_cf_fb'
K_MAIN_BC_LFINFO = 'kmain_bc_lfinfo'
K_MAIN_BC_LF_T = 'kmain_bc_lf_t'
K_MAIN_BC_LF_FB = 'kmain_bc_lf_fb'
K_MAIN_SC_CB = 'kmain_sc_cb'
K_MAIN_SC_CB_T = 'kmain_sc_cb_t'
K_MAIN_IT_LF = 'kmain_it_lf'
K_MAIN_IT_LD = 'kmain_it_ld'
K_MAIN_IT_RC = 'kmain_it_rc'
K_MAIN_IT_VPN_CF = 'kmain_it_vpn_cf'
K_MAIN_IT_BC_CF = 'kmain_it_bc_cf'
K_MAIN_IT_BC_LF = 'kmain_it_bc_lf'
K_MAIN_RAA_B = 'kmain_raa_b'
K_MAIN_RAA_T = 'kmain_raa_t'
K_MAIN_STP_B = 'kmain_stp_b'
K_MAIN_STP_T = 'kmain_stp_t'
K_MAIN_WIZ_B = 'kmain_wiz_b'
K_MAIN_WIZ_T = 'kmain_wiz_t'
K_MAIN_RBC_B = 'kmain_rbc_b'
K_MAIN_RBC_T = 'kmain_rbc_t'
K_MAIN_LOG = 'kmain_log'
K_MAIN_LOG_CB = 'kmain_log_cb'
K_MAIN_LIC = 'kmain_lic'

TT_MAIN_LF = 'Log file path'
TT_MAIN_LD = 'Loot directory path'
TT_MAIN_RC = 'Resources script file path'
TT_MAIN_VPN_CF = 'OpenVPN configuration file path'
TT_MAIN_BC_CF = 'Blockchain network configuration file path'
TT_MAIN_BC_LF = 'Blockchain log file path'
TT_MAIN_FB = 'File Browser'
TT_MAIN_DB = 'Folder Browser'
TT_MAIN_RAA = 'Run AutoAuditor'
TT_MAIN_STP = 'Stop Containers'
TT_MAIN_WIZ = 'Launch Helper'
TT_MAIN_RBC = 'Store in Blockchain'

T_MAIN_LF = 'Log File'
T_MAIN_LD = 'Log Directory'
T_MAIN_RC = 'Resources Script File'
T_MAIN_RC_CB = 'Edit Resources Script File'
T_MAIN_VPN_CF = 'OpenVPN Configuration File'
T_MAIN_VPN_CB = 'Enable VPN'
T_MAIN_BC_CF = 'Blockchain Configuration File'
T_MAIN_BC_CB = 'Enable Blockchain'
T_MAIN_BC_LF = 'Blockchain Log File'
T_MAIN_SC_CB = 'Stop container(s) after execution'
T_MAIN_RAA = 'Start'
T_MAIN_WIZ = 'Wizard'
T_MAIN_STP = 'Stop'
T_MAIN_RBC = 'Store'

DEF_MAIN_LF = os.path.abspath('output/msf.log')
DEF_MAIN_LD = os.path.abspath('output')
DEF_MAIN_RC = os.path.abspath('../config/rc.example.5vuln.json')
DEF_MAIN_VPN_CF = os.path.abspath('../config/client.example.ovpn')
DEF_MAIN_BC_CF = os.path.abspath('../config/network.example.json')
DEF_MAIN_BC_LF = os.path.abspath('output/blockchain.log')
DEF_MAIN_LIC = os.path.abspath('../LICENSE')

# WIZ Window
K_WIZ_MODT = 'kwiz_mtype'
K_WIZ_MODN = 'kwiz_mname'
K_WIZ_MODN_INFO = 'kwiz_mname_info'
K_WIZ_MODN_INFO_COL = 'kwiz_mname_info_col'
K_WIZ_EXIT = 'kwiz_exit'
K_WIZ_GEN = 'kwiz_gen'
K_WIZ_MCOL = 'kwiz_mcol'
K_WIZ_MADD = 'kwiz_madd'
K_WIZ_MEDIT = 'kwiz_medit_'
K_WIZ_MREM = 'kwiz_mrem_'
K_WIZ_MINFO = 'kwiz_minfo_'
K_WIZ_MFRAME = 'kwiz_mframe_'
K_WIZ_MNAME = 'kwiz_mname_'
TT_WIZ_MNAME = 'Module info'
TT_WIZ_MADD = 'Add module'
TT_WIZ_MEDIT = 'Edit module'
TT_WIZ_MREM = 'Remove module'
TT_WIZ_MINFO = 'Module info'
T_WIZ_TIT = 'Wizard'
T_WIZ_MTYPE = 'Module Type'
T_WIZ_MNAME = 'Module Name'
T_WIZ_MINFO_TIT = 'Module Info'
T_WIZ_GEN = 'Generate Resources Script'
T_WIZ_EXIT = 'Exit Wizard'

# MOPTS Window
K_MOPTS_TIT = 'kmopts_title'
K_MOPTS_ID = 'kmopts_id'
K_MOPTS_COL = 'kmopts_col'
K_MOPTS = 'kmopts_'
K_MOPTS_VAL = 'kmopts_val_'
K_MOPTS_INFO = 'kmopts_info_'
K_MOPTS_ACPT = 'kmopts_acpt'
K_MOPTS_CNCL = 'kmopts_cncl'
K_MOPTS_PADD = 'kmopts_padd'
K_MOPTS_PEDIT = 'kmopts_pedit'
K_MOPTS_PREM = 'kmopts_prem'
K_MOPTS_PINFO = 'kmopts_pinfo'
K_MOPTS_PDD = 'kmopts_pdd'

T_MOPTS_TIT = 'Module Options'
T_MOPTS_HNAME = 'Option Name'
T_MOPTS_HREQ = 'Required'
T_MOPTS_HVAL = 'Current Setting'
T_MOPTS_HINFO = 'Info'
T_MOPTS_INFO_TIT = 'Module Option Info'
T_MOPTS_RY = 'Yes'
T_MOPTS_RN = 'No'
T_MOPTS_PAY = 'Add payload ...'
T_MOPTS_PINFO_TIT = 'Payload Info'
TT_MOPTS_PADD = 'Add payload'
TT_MOPTS_PEDIT = 'Edit payload'
TT_MOPTS_PREM = 'Remove payload'
TT_MOPTS_PINFO = 'Payload info'

# POPTS Window
K_POPTS_TITLE = 'kpopts_title'
K_POPTS_ID = 'kpopts_id'
K_POPTS_COL = 'kpopts_col'
K_POPTS = 'kpopts_'
K_POPTS_VAL = 'kpopts_val_'
K_POPTS_INFO = 'kpopts_info_'
K_POPTS_ACPT = 'kpopts_acpt'
K_POPTS_CNCL = 'kpopts_cncl'

T_POPTS_TIT = 'Payload Options'
T_POPTS_INFO_TIT = 'Payload Option Info'

# Magic numbers
MAX_MODS = 50
C_EL = 10
C_OPTS = 13

C = {
    'white': '#ffffff',
    'blue': '#0079d3',
    'darkblue': '#4ca1e0',
    'lightblue': '#e9f6ff',
    'greyblue': '#d2dce4',
    'grey': '#808080',
    'lightgrey': '#e5e5e5',
    'black': '#000000',
    'red': '#ff0000'
}

B_C = (C['white'], C['white'])
B_C_ERR = (C['white'], C['red'])
B_SZ16 = (16, 16)
B_SZ24 = (24, 24)
B_SZ32 = (32, 32)
B_SZ48 = (48, 48)
P_ACTION = ((10, 10), (10, 0))
P_AB = ((5, 5), (60, 5))
P_MN = ((27, 5), (5, 5))
P_DD = ((38, 5), (5, 5))
P_T = ((5, 5), (10, 0))
P_IT = ((5, 5), (2, 0))
P_IT2 = ((5, 4), (6, 0))
P_IT2DD = ((5, 1), (6, 0))
P_IT3 = ((25, 1), (2, 2))
P_IT4 = ((6, 4), (2, 2))
P_IT5 = ((2, 1), (2, 2))
P_IT6 = ((29, 0), (2, 2))
P_IT7 = ((7, 0), (2, 2))
P_IT8 = ((5, 23), (6, 0))
P_HEAD_ONAME = ((27, 1), (0, 0))
P_HEAD_OVAL = ((12, 1), (0, 0))
P_HEAD_OREQ = ((12, 2), (0, 0))
P_HEAD_OINFO = ((18, 0), (0, 0))
P_N = ((0, 0), (0, 0))
P_N_TB = ((5, 5), (0, 0))
P_N_LR = ((0, 0), (5, 5))
P_N_L = ((0, 5), (5, 5))
P_N_R = ((5, 0), (5, 5))
P_N_R2 = ((7, 0), (5, 5))
P_N_R3 = ((5, 0), (3, 0))
P_N_RTB = ((12, 4), (0, 0))
P_N_TB3 = ((14, 0), (0, 0))
P_N_LRT = ((0, 0), (0, 5))
P_N_LRB = ((0, 0), (10, 0))
P_MOD = ((39, 7), (0, 0))
P_MOD2 = ((27, 7), (0, 0))
P_LOG = ((0, 0), (10, 20))
T_ACTION_SZ = (7, 1)
T_ACTION_SZ2 = (10, 1)
T_INFO_SZ = (15, 1)
T_INFO_SZ2 = (10, 2)
T_INFO_SZ3 = (50, 2)
T_INFO_SZ4 = (66, 2)
T_MODDD_SZ = (45, 1)
T_DESC_SZ = (27, 1)
T_DESC_SZ2 = (30, 1)
T_DESC_SZ3 = (39, 1)
T_DESC_SZ4 = (40, 1)
T_DESC_SZ5 = (64, 1)
T_DESC_SZ6 = (450, 1)
T_HEAD_ONAME_SZ = (24, 1)
T_HEAD_OVAL_SZ = (36, 1)
T_HEAD_OREQ_SZ = (8, 1)
C_SZ = (880, 320)
C_SZ2 = (880, 400)
C_SZ3 = (886, 400)
C_LOG_SZ = (106, 9)
C_TLOG_SZ = (85, 1)


def column_size(n_elem):
    return 894, C_SZ2[1]//C_OPTS * n_elem


FNT = ('TkDefaultFont', 12)
FNT2 = ('TkDefaultFont', 10)
FNT_B = ('TkDefaultFont', 12, 'bold')
FNT_P = 'Any 2'
FNT_P2 = ('TkDefaultFont', 55)

N_WDTH = 0
J_C = 'center'
T_N = ''
