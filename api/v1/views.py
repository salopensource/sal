from django.http import HttpResponseGone


UNICORN = r"""
                             \
                              \
                               \\
     API V1 is gone forever!    \\
     Just like me!               >\/7
      Laters...              _.-(6'  \
                            (=___._/` \
                                 )  \ |
                                /   / |
                               /    > /
                              j    < _\
                          _.-' :      ``.
                          \ r=._\        `.
                         <`\\_  \         .`-.
                          \ r-7  `-. ._  ' .  `\
                           \`,      `-.`7  7)   )
                            \/         \|  \'  / `-._
                                       ||    .'
                                        \\  (
                                         >\  >
                                     ,.-' >.'
                                    <.'_.''
                                      <'
"""


def deprecation_view(request):
    return HttpResponseGone(UNICORN, content_type="text/plain")
