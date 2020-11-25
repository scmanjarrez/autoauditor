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
OVPN_TEMPLATE = '../config/client.example.ovpn'

# GUI

WRAP_T_SZ = 90

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
ICO_BCKCHN = (b'iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAABHNCSVQICAgIfA'
              b'hkiAAAAAlwSFlzAAAOxAAADsQBlSsOGwAAABl0RVh0U29mdHdhcmUAd3d3Lmlu'
              b'a3NjYXBlLm9yZ5vuPBoAAAcOSURBVGiBxdlrsNVVGQbw30EMUMJATONoQpHZxW'
              b'oarERLM5MywkLI6EM22tikXabU7AoTkJOofWi0IqmmTKAIA5WszLykNRlqZlip'
              b'WHTBIq8DkYeE3Ydn7fbmz9nn7LPZ2Dtz5uz/2uu/1vus9b7Peta72dl+jNr/6W'
              b'8HPmKINrzy/FLci2uGOlAX7MN4ye4OshHf3n1fOrJHsWSoLw3HT/DK8rwfZuOk'
              b'7vkFnsAHsKbL4xqON+AP+E23By+2P47HVTgF13Z7ghou6vagTTa1zLEVfZjeol'
              b'/HIdSOTcBbcTR6MRL/xF24Dre3McZHcRZW4h1YPVRnW9lAO9Arq/JU6fewOH0b'
              b'Ngj11fALHNtijPoOnIIDJFT7cHKlX0c7MBCA1xeH/4PFmIKeSp9DcA42YTvm99'
              b'OnGYABQHQVwAnYhgdwRBtjjMGKMtYXKt/VAdyN68vfnaWtr3xPFwFMKoPdh/FD'
              b'GKcHXyvjzWlqH49fYn3l78HSd0Hp1zUAy/FvHN7m+/PxovL5GfgVHpFdGchG6g'
              b'KAYZXnFwpDfAm/b+P9afiMxsG3TXJiHN47VGc6sSqAmRIKX27z/U9Loi9uarsF'
              b'v8WpTW1T8EPcbFf22S2rngPHSuw/0Ma703AMzsWWync/kJ2YI+x0KfbCZkn2l+'
              b'FPnTrdbFUAvfhjm+/2t/p1e1AcXtrU9iE5Q36GI+0hAGNEFw1mA62+prZ3l/FW'
              b'YWFp3yYHX1esmgOP4qB++p2OFzc9z8M/tM6V55T/t4rMmIYbcI9IknZCtC2r7s'
              b'A9eLtQ3JOlbSwulFg+HgfjKFn9rS3GfbVI6A1N487sltPNVt2B6zAab2pqewxv'
              b'FLA/lTNjoNV/pqz4StFKcyRPTu9nvq5Y80E2Cg9JslUne7ko0JowTCubX/pMl0'
              b'tMTeK+JmdG3bpykFUBwJmlbV4/fY8QStynxVivkdBrvqxvwAislYXZ4wB6hDV2'
              b'yEW7XTsSf8df8XGcjx+JFF8q+bK8qf8eAwD7yl25ViY9dID3RxVntxYAzRpqrF'
              b'Q4tkjJprcfANeJgu2TosIq2eUzNdhsyACIMPtK+f5JXI2zJbZPEI5fXJyuyek7'
              b'oZ0JRXNdoRFmffiLhNn9+Fdp3y7EcVQnAAht1kTfPGzn2K4DWy2sVb3I9GfD8S'
              b'lJ6j5cjhNlsZqtR0LygjLvDlwpkdERgJNEGkyW0shmSei923C6biMFbE3CZFKL'
              b'+S7Dx6TIBs/CxQXEr+UW2BaA0fhe+X61hr5fIgk3FBsmubADc7XerVM1wqcmp/'
              b'hx5buZkkv3Sv1qUABf1IjBpzREWycA5pV55rbZf5Kc9A8J6AUC+s3Fl2s1LUIr'
              b'ADdrXGrulmshQwdwmMT7KgPnycGyaK9qahuNZcXHS0rbJ8vz/6RJKwD1jnWWmd'
              b'8hgKUFQH8xX7d9ROCdiXWS2HXrwdeLD7Mk4dfL4u41EIDhUu5ejfMkYadrlFAu'
              b'NDjzjBemurzSPqyM/VU8DwcKy6wRuXGarP5FWCRX1HvlnjECZxS/XzcQgKqNwu'
              b'NyY1ujoXcGsjml34mV9rm4EZ/H76Qifq6UWxaIULxTdu9KIZNZGvWlcVKvuqTd'
              b'0iI5VfeTw+37Qq0TB3nnaOH8myrte0tsHyda6X3CPi+QHegpc9xXPh8qLLYZM0'
              b'TprsXUocjbjXIdPF9Ki1sMXmk+RJhkW6X9sxI2E6UCsgTfFMZZJqu+QgjgMNmd'
              b'PhGDdamyAb1D2QGy6mdJbH/D4Pfa/eQkJWX8g4pzT4n+GS8S5WZZjCckv5YXIH'
              b'2yA/UxluK55fMmPHuoALZIUrVrW4UeSeyeVgDA20QTHYhPFCcPwN/wFtnt10rC'
              b'XyXAmgsIY/FYFcAtZZBO7Tw7h9VDUqrpkWrHPkKnpwiPr8HPpZh2h6zwe4pzVw'
              b'u11iTJm8uVRNlurAL4s/6rDO1a9d21cpWcIrJ5UXF+f4n7aaJv7sLzZbemStLf'
              b'XwAMs6v+GSUH3nfZs7/QTJTEvKA83y67MkEE2vX4YHFkPd4vVb1r5SBdJvkwuT'
              b'LujOL3yT3lw8Wy/StkdTq1z0n5pNluFOU6Ga8QbfUdvKvMrcxZv6reIeF2xQDz'
              b'3Cr5c2iVRseIfO30r6rriQTZXyp5NxWQ75RS/IjS5xHh/dFCuUt3GaVhs+V8Wa'
              b'iUdfb0j3yEeXZI4g4TYVYTeTBLA8hgdriogXXKYlWT+FJhgE7tMmGVqp0t4fMt'
              b'WcFzpLy4SMJ2syTzMq3rTYcLa22XCve2/gAcI7zcqa1s0f64XDtvEEkwV/LuGt'
              b'FTM5SYbvH+bBGE2+X82Kk0+XSEUN3GCZ3WhHXO0Jo0Rgmw20r/dXZlI3UWul3Y'
              b'4umyWcL7RFasFW2zScigV+qr+8oJvVBCq6qp9MhPnu38ErknbLvE9YFyLxgrDt'
              b'fLm1fLWdGqiOy/4wMqPaaaYfIAAAAASUVORK5CYII=')
ICO_CBOFF = (b'iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAABHNCSVQICAgIfAh'
             b'kiAAAAAlwSFlzAAAAygAAAMoBawMUsgAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3'
             b'NjYXBlLm9yZ5vuPBoAAABsSURBVEiJ7dahEYNQFETRQ1RaIPGpgxZphYCnjjTyc'
             b'T+CLxgG+XBvZ9beK3fhjQUFNagFM14aPAp87tw12xM/rGIy4IPNwTYGwTVWRX0E'
             b'Qi+TghSkIAUpSAHcPZmFff3vGv2J/Vp8xd+WCf0fuZVmwe+b7gsAAAAASUVORK5'
             b'CYII=')
ICO_CBON = (b'iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAABHNCSVQICAgIfAhk'
            b'iAAAAAlwSFlzAAAAxwAAAMcBYjN5IQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3Nj'
            b'YXBlLm9yZ5vuPBoAAAEoSURBVEiJ1daxLgRBGMDxH1Hc4QXwChqVRCtatYI3UEiI'
            b'oLhGo5MrNJKrPIFzGkKCxBN4EQWrW8XuyRq7t3cyV9yXTPN9k/9/dne+nYEl3CJB'
            b'Gmkk6GFRDo8FDkdvKrc18IZXcWINy/hSsLUjweWsFOl0RGhpTISgiSvslhVnIsCv'
            b'sYFt2YbpxBLMoov1Qq4RTvrvKyqDt3AxrGAFOxW1OVlzFuHHOK1aTdgHq3jPcyfB'
            b'3Hk8+d2thyXMdqH+R3AeAI4K8OegdlCx6IGCJu4CUAsvQW6/Al4r6EvuA2DZU9UK'
            b'qj5ygk08BPkUezirEfzEoG3alzwG8JF+inWN9plLOrnochT4MAL4wNao4H5MxN90'
            b'YIz7yEzITv9xHfpdsqvFjfjXli4WvgFlkbAzkqReWwAAAABJRU5ErkJggg==')
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
ICO_C_H = (b'iVBORw0KGgoAAAANSUhEUgAAAA8AAAAYCAYAAAAlBadpAAAABHNCSVQICAgIfAhki'
           b'AAAAAlwSFlzAAAAsQAAALEBxi1JjQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYX'
           b'BlLm9yZ5vuPBoAAABgSURBVDiN7dChDYAwFAbhT2BogmUyRoDtYAVCwkgMAIa6pmk'
           b'xCLjkd+9OPH6+TosBoVYMWHFiR/dEjCsKpMSiQE7MBkrEZCBgKxTjttszVYpxY4MZ'
           b'fe4ZCQ4sFfc/73IB07s9/4Aha1cAAAAASUVORK5CYII=')
ICO_ADD = (b'iVBORw0KGgoAAAANSUhEUgAAACoAAAAwCAYAAABnjuimAAAABHNCSVQICAgIfAhki'
           b'AAAAAlwSFlzAAABYgAAAWIBXyfQUwAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYX'
           b'BlLm9yZ5vuPBoAAAFVSURBVFiF7Zk/TsMwFIe/pAykgoEDMHEDuEAP0I0FhLgEO+J'
           b'Pd8QluvYWtEPFCRohbsCCQEiJYAhDBIqfVf2IU+JP8hI7fp/iF9uJIdJzhsAtkAMF'
           b'8Bm4FN8uN0BWl1x0QK6pzIFsAFwCZ/4Pv3X2gSKhesQHgWUs8oQqHwahTQzKhCoPO'
           b'k8aWsCXLVE/OTDj9+gkwDGid0AxhYwd/Y8VMVRD/7pmnTcbk6NRVE0UVRNF1VhrfQ'
           b'5cAO9GP4/AS0PdHnBk3D8E7jBWMNeKMDECKJm4XKyhL//WzT/WxuRoFFVjibb5ieK'
           b'MZW2cT4Al8Ga0U0xPp0YbycZ55Oh/pIjxb3K0M0RRNVFUTe9Edxx1u4oAql8698Ah'
           b'8PHj+jZwrggQ/+apSWl3F78uZQo8h7bw4CkFpqEtPJhCdY4zJ/wxTVN5oHbWlAHXw'
           b'IruHIitgKu6ZKSXfAGaqgy+iuM3xwAAAABJRU5ErkJggg==')
ICO_ADD_S = (b'iVBORw0KGgoAAAANSUhEUgAAABUAAAAYCAYAAAAVibZIAAAABHNCSVQICAgIfAh'
             b'kiAAAAAlwSFlzAAAAsQAAALEBxi1JjQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3'
             b'NjYXBlLm9yZ5vuPBoAAADRSURBVDiN7dWxagJBEMbx3xlTaqdN6iSdlY0PoJWgT'
             b'6ZdWp8hkN4XEHvxEaxOSwVTuMJ6RO4S9oqAf1iWWXY+ZmeWGWogC2uKtwR6G3zC'
             b'HOeEa5YhRztBlFfyLKgnpVHhzhojDMO+riJclqNF4f6izKdKpL/m/4gWq7/FGKf'
             b'o7IBdZHfQiuwmvvAaC8dJXv4xuKW6C9Us2C94xzE6K3v+c/C74fFP01Is1E/0XJ'
             b'rJ2eVf98ocamt9+8Sa+RO6GCQU/bgOvgn6quX4HieshMGXnG9w7FckggmoLQAAA'
             b'ABJRU5ErkJggg==')
ICO_EDIT = (b'iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAABHNCSVQICAgIfAhk'
            b'iAAAAAlwSFlzAAABLQAAAS0B1sg7IAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3Nj'
            b'YXBlLm9yZ5vuPBoAAADkSURBVFiF7dcxCsIwFMbx/6DHcnB1dfIGnV0LpW528ByC'
            b'6OgVvIRb0UlxEUFE0CEGSqltWl8ShDx4UGjp70vS0gZC2asIOAIXIAP6LvEZ8Cr1'
            b'xlWIKtxZiLgG1722GWII3AxCZNJwAoxbhDhL4nrNHy1C5NK4btMQkQSefrn5E5h8'
            b'rhkA19L5uU28KYQIXvee1y1HLIGnhnjVTPxcpiMvd+ITd7rmAQ/4/+OjjvhMAgeY'
            b'dsBFRq5r4RMHWPnEAXY+cVC/Sd5wgHsDLva0F6tXOF6ivt0n1GwcUFurHNgDWxsB'
            b'Qr0BZ6w2bYtcY1sAAAAASUVORK5CYII=')
ICO_REM = (b'iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAABHNCSVQICAgIfAhki'
           b'AAAAAlwSFlzAAABDAAAAQwBlqf4UAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYX'
           b'BlLm9yZ5vuPBoAAAD6SURBVFiF7ZYxEoIwEEWf2nkJ9B5AgTbewBvoUbimvYUzDLZ'
           b'YmMyog8luXEnDn0lFNu+RkBCYkzmrwLMaOABX4JY4/hY4AmvgoilsgcG1DmgS4I2r'
           b'9eO0KXDfeqVE42o+x4lK1CNFWolvcN/KUPE5UCiRiMEH4BQSKHhfN42EBN45RjCVQ'
           b'OIO7F9qaqH4LgZPkTCH+0imtBf2SdnGgGwmzN/cSsIEniphCtdKqOBLhcBC0U/aVx'
           b'zJVgudE5PCTSVS4SYSWQ8izfGa8u8wg/uYSWyE8L/9jrNfSKof4FKJ4JUMMl9KxyQ'
           b'mv5b7lDzXK/jRRFK4MaLTPidbHqpgYJKLVQy1AAAAAElFTkSuQmCC')

LOADING = '../autoauditor/gui_files/loading.gif'
FONT = ('../autoauditor/gui_files/Hack-Regular.ttf', 12)
FONT_S = ('../autoauditor/gui_files/Hack-Regular.ttf', 11)
FONTB = ('../autoauditor/gui_files/Hack-Regular.ttf', 12, 'bold')
FONTP = 'Any 2'

T_REQ_SZ = (8, 1)
T_HEAD_REQ_SZ = (5, 1)
T_DESC_SZ_S = (27, 1)
T_DESC_SZ_S2 = (30, 1)
T_DESC_SZ_M = (50, 1)
T_DESC_SZ_M2 = (79, 1)
T_DESC_SZ_XL = (558, 1)
T_DESC_SZ_XL2 = (566, 1)
T_OPT_NAME_SZ = (25, 1)
T_OPT_VAL_SZ = (46, 1)

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
MAIN_ABOUT_VER = 'v1.0'
MAIN_ABOUT_AUTHOR = 'Sergio Chica Manjarrez'
MAIN_ABOUT_LAB = 'Pervasive Computing Laboratory'
MAIN_ABOUT_DEPT = "Telematic Engineering Department"
MAIN_ABOUT_UC3M = 'Universidad Carlos III de Madrid, Leganés'
MAIN_ABOUT_LOC = 'Madrid, Spain'
MAIN_ABOUT_ACK = """This work has been supported by National R&D Projects TEC2017-84197-C4-1-R,
TEC2014- 54335-C4-2-R, and by the Comunidad de Madrid project CYNAMON
P2018/TCS-4566 and co-financed by European Structural Funds (ESF and FEDER)."""
MAIN_ABOUT_YEAR = date.today().strftime('%Y')
MAIN_LIC_T_SZ = (105, 675)
MAIN_LIC_C_SZ = (950, 280)

K_MAIN_LFINFO = 'kmain_lfinfo'
K_MAIN_LF_FB = 'kmain_lf_fb'
K_MAIN_LDINFO = 'kmain_ldinfo'
K_MAIN_LD_FB = 'kmain_ld_fb'
K_MAIN_RCINFO = 'kmain_rcinfo'
K_MAIN_RC_FB = 'kmain_rc_fb'
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

TT_MAIN_LF = ('Absolute path to log file where output should be written. '
              'Click for more details.')
TT_MAIN_LD = ('Absolute path to directory where gathered data '
              'should be collected. Click for more details.')
TT_MAIN_RC = 'Absolute path to resources script file. Click for more details.'
TT_MAIN_VPN_CF = ('Absolute path to openvpn configuration file. '
                  'Click for more details.')
TT_MAIN_BC_CF = ('Absolute path to blockchain network configuration file. '
                 'Click for more details.')
TT_MAIN_BC_LF = ('Absolute path to blockchain log file '
                 'where output should be written. Click for more details.')
TT_MAIN_FB = 'File Browser'
TT_MAIN_DB = 'Folder Browser'
TT_MAIN_RAA = 'Run AutoAuditor'
TT_MAIN_STP = 'Stop Containers'
TT_MAIN_WIZ = 'Launch Helper'
TT_MAIN_RBC = 'Store in Blockchain'

T_MAIN_LF = 'Log File'
T_MAIN_LD = 'Log Directory'
T_MAIN_RC = 'Resources Script File'
T_MAIN_VPN_CB = 'Enable VPN'
T_MAIN_VPN_CF = 'OpenVPN Configuration File'
T_MAIN_BC_CB = 'Enable Blockchain'
T_MAIN_BC_CF = 'Blockchain Configuration File'
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
K_WIZ_MODT = 'kwiz_mod_type'
K_WIZ_MODN = 'kwiz_mod_name'
# K_MTYPE_INFO = 'key_mtype_info'
# K_MNAME_INFO = 'key_mname_info'
K_WIZ_EXIT = 'kwiz_exit'
K_WIZ_GEN = 'kwiz_gen'
K_WIZ_MCOL = 'kwiz_mcol'
K_WIZ_MADD = 'kwiz_madd'
K_WIZ_MEDIT = 'kwiz_medit_'
K_WIZ_MREM = 'kwiz_mrem_'
K_WIZ_MINFO = 'kwiz_minfo_'
K_WIZ_MFRAME = 'kwiz_mframe_'
K_WIZ_MNAME = 'kwiz_mname_'
# TT_WIZ_MTYPE = 'Module type. Click for more details'
# TT_WIZ_MNAME = 'Module name. Click for more details'
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
K_MOPTS = 'kmopts_'
K_MOPTS_VAL = 'kmopts_val_'
K_MOPTS_INFO = 'kmopts_info_'
K_MOPTS_ACPT = 'kmopts_acpt'
K_MOPTS_CNCL = 'kmopts_cncl'
K_MOPTS_PAY = 'kmopts_pay'
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
K_POPTS = 'kpopts_'
K_POPTS_VAL = 'kpopts_val_'
K_POPTS_INFO = 'kpopts_info_'
K_POPTS_ACPT = 'kpopts_acpt'
K_POPTS_CNCL = 'kpopts_cncl'

T_POPTS_TIT = 'Payload Options'
T_POPTS_INFO_TIT = 'Payload Option Info'

K_GIF = 'gif'

MAX_OPTS = 100
MAX_MODS = 50

C_EN = 'black'
C_DIS = 'grey'
C_W = 'white'
C_TAB_DIS = 'gray90'
B_C = ('white', 'white')
B_C_ERR = ('white', 'red')
B_SZ_S = (24, 24)
B_SZ_M = (32, 32)
B_SZ_L = (48, 48)
P_EXEC_T = ((10, 10), (10, 0))
P_T = ((5, 5), (10, 0))
P_IT = ((5, 5), (2, 0))
P_IT2 = ((7, 5), (6, 0))
P_IT3 = ((7, 5), (2, 2))
P_IT4 = ((5, 3), (2, 2))
P_IT5 = ((5, 2), (2, 2))
P_IT6 = ((2, 2), (2, 2))
P_IT7 = ((26, 5), (2, 2))
P_IT7_NS = ((18, 5), (2, 2))
P_IT_TR = ((5, 23), (6, 0))
P_IT_TR2 = ((5, 17), (6, 0))
P_OPT_HEAD_NAME = ((5, 5), (0, 0))
P_OPT_HEAD_VAL = ((6, 4), (0, 0))
P_OPT_HEAD_REQ = ((8, 15), (0, 0))
P_OPT_HEAD_REQ2 = ((8, 10), (0, 0))
P_OPT_HEAD_INFO = ((3, 0), (0, 0))
N_P = ((0, 0), (0, 0))
N_P_TB = ((5, 5), (0, 0))
N_P_LR = ((0, 0), (5, 5))
N_P_L = ((0, 5), (5, 5))
N_P_R = ((5, 0), (5, 5))
N_P_TBR = ((10, 0), (0, 0))
N_P_LRB = ((0, 0), (10, 0))
N_P_LB = ((0, 24), (10, 0))
N_P_LB_NS = ((0, 15), (10, 0))
P_MOD = ((28, 0), (0, 0))
LOG_P = ((0, 0), (10, 20))
LOG_SZ = (80, 8)
LOG_CB_P_SZ = (110, 1)
EXEC_T_SZ_S = (10, 1)
EXEC_T_SZ_XS = (15, 1)
EXEC_T_SZ_M = (30, 1)
EXEC_T_SZ_L = (60, 1)
EXEC_T_SZ_L2 = (49, 1)

C_SZ = (1128, 495)


def column_size(n_elem): return (1128, 33 * n_elem)


N_WDTH = 0
J_C = 'center'
N_T = ''
