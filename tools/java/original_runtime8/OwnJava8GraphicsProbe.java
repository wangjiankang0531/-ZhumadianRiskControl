package xnby.platform;
import java.nio.file.*;
import java.util.*;
import java.awt.*;
import java.awt.image.BufferedImage;
import javax.imageio.ImageIO;
import xnby.replica.OriginalProcessBoundary;
/** Exercise only installed JDK font/PNG support; never generate or solve a CAPTCHA. */
public final class OwnJava8GraphicsProbe {
 public static void main(String[] args)throws Exception{
  Path root=Paths.get(args[0]).toRealPath();
  OriginalProcessBoundary guard=new OriginalProcessBoundary(root,Collections.singleton(40000),false);
  System.setSecurityManager(guard);
  BufferedImage image=new BufferedImage(100,40,BufferedImage.TYPE_INT_RGB);
  Graphics2D graphics=image.createGraphics();
  try{graphics.setColor(Color.WHITE);graphics.fillRect(0,0,100,40);graphics.setColor(Color.BLACK);graphics.setFont(new Font("SansSerif",Font.PLAIN,16));graphics.drawString("probe",8,24);}
  finally{graphics.dispose();}
  if(!ImageIO.write(image,"png",root.resolve("jdk-font-probe.png").toFile()))throw new IllegalStateException("PNG_WRITER_MISSING");
  if(!ImageIO.write(image,"jpg",root.resolve("jdk-font-probe.jpg").toFile()))throw new IllegalStateException("JPEG_WRITER_MISSING");
  System.out.println("JDK_GRAPHICS_PROBE PASS");
 }
}
